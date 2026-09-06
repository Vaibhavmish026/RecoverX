#!/usr/bin/env python
"""RecoverX Development Seed Data Script.

Populates and verifies a complete synthetic development relationship graph:
Merchant -> Customer -> Transaction -> RecoveryCase -> RecoveryAction -> AuditLog

Usage:
    python scripts/seed_dev_data.py
    python scripts/seed_dev_data.py --clean
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Ensure backend root is on PYTHONPATH
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(CURRENT_DIR)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    ActionStatus,
    ActionType,
    ActorType,
    AuditLog,
    CaseStatus,
    Customer,
    Merchant,
    RecoveryAction,
    RecoveryCase,
    Transaction,
    TransactionStatus,
)

SEED_MERCHANT_EMAIL = "demo@recoverx-merchant.test"


def clean_seed_data(db: Session) -> None:
    """Removes existing seed records specifically associated with the test merchant."""
    merchant = db.scalar(
        select(Merchant).where(Merchant.email == SEED_MERCHANT_EMAIL)
    )
    if merchant:
        print(f"[CLEAN] Found existing seed merchant: {merchant.email} ({merchant.id})")
        # Find cases to clean associated audit logs
        cases = db.scalars(
            select(RecoveryCase).where(RecoveryCase.merchant_id == merchant.id)
        ).all()
        case_ids = [c.id for c in cases]
        if case_ids:
            audit_logs = db.scalars(
                select(AuditLog).where(AuditLog.case_id.in_(case_ids))
            ).all()
            for log in audit_logs:
                db.delete(log)
            print(f"[CLEAN] Removed {len(audit_logs)} associated audit logs.")

        db.delete(merchant)
        db.flush()
        print("[CLEAN] Removed test merchant and all cascaded entities.")
    else:
        print("[CLEAN] No existing seed merchant found to clean.")


def seed_data(db: Session, clean: bool = False) -> None:
    """Seeds synthetic test data idempotently."""
    now = datetime.now(timezone.utc)

    if clean:
        clean_seed_data(db)

    print("\n--- SEEDING RECOVERX DEVELOPMENT DATA ---")

    # 1. MERCHANT
    merchant = db.scalar(
        select(Merchant).where(Merchant.email == SEED_MERCHANT_EMAIL)
    )
    if not merchant:
        merchant = Merchant(
            name="Acme Retail Store (Dev Workspace)",
            email=SEED_MERCHANT_EMAIL,
            is_active=True,
            razorpay_account_id="acc_test_recoverx_01",
            config={
                "max_retry_attempts": 3,
                "discount_cap_percent": 10,
                "auto_recovery_enabled": True,
                "allowed_channels": ["payment_link", "smart_retry", "whatsapp"],
            },
        )
        db.add(merchant)
        db.flush()
        print(f"[CREATED] Merchant: {merchant.name} ({merchant.id})")
    else:
        merchant.name = "Acme Retail Store (Dev Workspace)"
        merchant.is_active = True
        merchant.razorpay_account_id = "acc_test_recoverx_01"
        merchant.config = {
            "max_retry_attempts": 3,
            "discount_cap_percent": 10,
            "auto_recovery_enabled": True,
            "allowed_channels": ["payment_link", "smart_retry", "whatsapp"],
        }
        db.flush()
        print(f"[REUSED] Merchant: {merchant.name} ({merchant.id})")

    # 2. CUSTOMERS
    customers_data = [
        {
            "external_customer_id": "cust_ext_1001",
            "name": "Aarav Sharma (Test)",
            "email": "aarav.test@example.com",
            "phone": "+919876543210",
        },
        {
            "external_customer_id": "cust_ext_1002",
            "name": "Priya Patel (Test)",
            "email": "priya.test@example.com",
            "phone": "+919876543211",
        },
    ]

    customers_map = {}
    for c_data in customers_data:
        cust = db.scalar(
            select(Customer).where(
                Customer.merchant_id == merchant.id,
                Customer.external_customer_id == c_data["external_customer_id"],
            )
        )
        if not cust:
            cust = Customer(
                merchant_id=merchant.id,
                external_customer_id=c_data["external_customer_id"],
                name=c_data["name"],
                email=c_data["email"],
                phone=c_data["phone"],
            )
            db.add(cust)
            db.flush()
            print(f"[CREATED] Customer: {cust.name} ({cust.external_customer_id})")
        else:
            cust.name = c_data["name"]
            cust.email = c_data["email"]
            cust.phone = c_data["phone"]
            db.flush()
            print(f"[REUSED] Customer: {cust.name} ({cust.external_customer_id})")
        customers_map[c_data["external_customer_id"]] = cust

    # 3. TRANSACTIONS
    tx1_data = {
        "customer_id": customers_map["cust_ext_1001"].id,
        "external_order_id": "order_test_2001",
        "external_payment_id": "pay_test_3001",
        "amount": Decimal("2499.00"),
        "currency": "INR",
        "payment_method": "upi",
        "failure_code": "GATEWAY_ERROR",
        "failure_reason": "Bank NPCI gateway timeout during UPI PIN validation",
        "status": TransactionStatus.FAILED,
        "raw_payload": {
            "gateway": "razorpay_mock",
            "error": {
                "code": "GATEWAY_ERROR",
                "description": "Bank NPCI gateway timeout during UPI PIN validation",
            },
        },
        "occurred_at": now - timedelta(hours=2),
    }

    tx2_data = {
        "customer_id": customers_map["cust_ext_1002"].id,
        "external_order_id": "order_test_2002",
        "external_payment_id": "pay_test_3002",
        "amount": Decimal("4999.00"),
        "currency": "INR",
        "payment_method": "card",
        "failure_code": "INSUFFICIENT_FUNDS",
        "failure_reason": "Card issuing bank reported temporary balance limit reached",
        "status": TransactionStatus.FAILED,
        "raw_payload": {
            "gateway": "razorpay_mock",
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "description": "Card issuing bank reported temporary balance limit reached",
            },
        },
        "occurred_at": now - timedelta(hours=4),
    }

    transactions_map = {}
    for tx_data in [tx1_data, tx2_data]:
        tx = db.scalar(
            select(Transaction).where(
                Transaction.merchant_id == merchant.id,
                Transaction.external_payment_id == tx_data["external_payment_id"],
            )
        )
        if not tx:
            tx = Transaction(
                merchant_id=merchant.id,
                customer_id=tx_data["customer_id"],
                external_order_id=tx_data["external_order_id"],
                external_payment_id=tx_data["external_payment_id"],
                amount=tx_data["amount"],
                currency=tx_data["currency"],
                payment_method=tx_data["payment_method"],
                failure_code=tx_data["failure_code"],
                failure_reason=tx_data["failure_reason"],
                status=tx_data["status"],
                raw_payload=tx_data["raw_payload"],
                occurred_at=tx_data["occurred_at"],
            )
            db.add(tx)
            db.flush()
            print(f"[CREATED] Transaction: {tx.external_payment_id} ({tx.amount} {tx.currency})")
        else:
            tx.customer_id = tx_data["customer_id"]
            tx.external_order_id = tx_data["external_order_id"]
            tx.amount = tx_data["amount"]
            tx.currency = tx_data["currency"]
            tx.payment_method = tx_data["payment_method"]
            tx.failure_code = tx_data["failure_code"]
            tx.failure_reason = tx_data["failure_reason"]
            tx.status = tx_data["status"]
            tx.raw_payload = tx_data["raw_payload"]
            tx.occurred_at = tx_data["occurred_at"]
            db.flush()
            print(f"[REUSED] Transaction: {tx.external_payment_id} ({tx.amount} {tx.currency})")
        transactions_map[tx_data["external_payment_id"]] = tx

    # 4. RECOVERY CASES
    case1_data = {
        "transaction_id": transactions_map["pay_test_3001"].id,
        "status": CaseStatus.IN_PROGRESS,
        "diagnostic_summary": (
            "AI Diagnostic: NPCI UPI system downtime detected during initial checkout. "
            "User purchase intent remains high."
        ),
        "root_cause_category": "bank_downtime",
        "confidence_score": Decimal("0.92"),
        "selected_strategy": "payment_link",
        "recovered_amount": None,
        "recovered_at": None,
        "expires_at": now + timedelta(hours=22),
    }

    case2_data = {
        "transaction_id": transactions_map["pay_test_3002"].id,
        "status": CaseStatus.RECOVERED,
        "diagnostic_summary": (
            "AI Diagnostic: Card attempt failed due to temporary limit. "
            "Smart retry triggered at optimal window succeeded."
        ),
        "root_cause_category": "insufficient_balance",
        "confidence_score": Decimal("0.85"),
        "selected_strategy": "smart_retry",
        "recovered_amount": Decimal("4999.00"),
        "recovered_at": now - timedelta(hours=1),
        "expires_at": now + timedelta(hours=20),
    }

    cases_map = {}
    for c_data in [case1_data, case2_data]:
        rc = db.scalar(
            select(RecoveryCase).where(
                RecoveryCase.transaction_id == c_data["transaction_id"]
            )
        )
        if not rc:
            rc = RecoveryCase(
                merchant_id=merchant.id,
                transaction_id=c_data["transaction_id"],
                status=c_data["status"],
                diagnostic_summary=c_data["diagnostic_summary"],
                root_cause_category=c_data["root_cause_category"],
                confidence_score=c_data["confidence_score"],
                selected_strategy=c_data["selected_strategy"],
                recovered_amount=c_data["recovered_amount"],
                recovered_at=c_data["recovered_at"],
                expires_at=c_data["expires_at"],
            )
            db.add(rc)
            db.flush()
            print(f"[CREATED] RecoveryCase: For TX {rc.transaction_id} (Status: {rc.status.value})")
        else:
            rc.status = c_data["status"]
            rc.diagnostic_summary = c_data["diagnostic_summary"]
            rc.root_cause_category = c_data["root_cause_category"]
            rc.confidence_score = c_data["confidence_score"]
            rc.selected_strategy = c_data["selected_strategy"]
            rc.recovered_amount = c_data["recovered_amount"]
            rc.recovered_at = c_data["recovered_at"]
            rc.expires_at = c_data["expires_at"]
            db.flush()
            print(f"[REUSED] RecoveryCase: For TX {rc.transaction_id} (Status: {rc.status.value})")
        cases_map[c_data["transaction_id"]] = rc

    # 5. RECOVERY ACTIONS
    case1 = cases_map[transactions_map["pay_test_3001"].id]
    case2 = cases_map[transactions_map["pay_test_3002"].id]

    actions_data = [
        # Action 1.1 under Case 1
        {
            "case_id": case1.id,
            "action_type": ActionType.RAZORPAY_PAYMENT_LINK,
            "status": ActionStatus.SUCCEEDED,
            "external_reference_id": "plink_test_9001",
            "action_payload": {
                "amount": 249900,
                "currency": "INR",
                "description": "Recovery link for order_test_2001",
            },
            "response_payload": {
                "id": "plink_test_9001",
                "short_url": "https://rzp.io/i/mock_recover_9001",
                "status": "issued",
            },
            "error_message": None,
            "scheduled_for": now - timedelta(minutes=105),
            "executed_at": now - timedelta(minutes=105),
        },
        # Action 1.2 under Case 1
        {
            "case_id": case1.id,
            "action_type": ActionType.WHATSAPP_NUDGE,
            "status": ActionStatus.SCHEDULED,
            "external_reference_id": None,
            "action_payload": {
                "template": "payment_retry_nudge",
                "recipient": "+919876543210",
            },
            "response_payload": None,
            "error_message": None,
            "scheduled_for": now + timedelta(hours=2),
            "executed_at": None,
        },
        # Action 2.1 under Case 2
        {
            "case_id": case2.id,
            "action_type": ActionType.SMART_RETRY,
            "status": ActionStatus.SUCCEEDED,
            "external_reference_id": "pay_test_retry_3002",
            "action_payload": {
                "retry_attempt": 1,
                "delay_minutes": 120,
            },
            "response_payload": {
                "status": "captured",
                "payment_id": "pay_test_retry_3002",
            },
            "error_message": None,
            "scheduled_for": now - timedelta(hours=2),
            "executed_at": now - timedelta(hours=1),
        },
    ]

    for a_data in actions_data:
        action = db.scalar(
            select(RecoveryAction).where(
                RecoveryAction.case_id == a_data["case_id"],
                RecoveryAction.action_type == a_data["action_type"],
            )
        )
        if not action:
            action = RecoveryAction(
                case_id=a_data["case_id"],
                action_type=a_data["action_type"],
                status=a_data["status"],
                external_reference_id=a_data["external_reference_id"],
                action_payload=a_data["action_payload"],
                response_payload=a_data["response_payload"],
                error_message=a_data["error_message"],
                scheduled_for=a_data["scheduled_for"],
                executed_at=a_data["executed_at"],
            )
            db.add(action)
            db.flush()
            print(f"[CREATED] RecoveryAction: {action.action_type.value} for Case {action.case_id}")
        else:
            action.status = a_data["status"]
            action.external_reference_id = a_data["external_reference_id"]
            action.action_payload = a_data["action_payload"]
            action.response_payload = a_data["response_payload"]
            action.error_message = a_data["error_message"]
            action.scheduled_for = a_data["scheduled_for"]
            action.executed_at = a_data["executed_at"]
            db.flush()
            print(f"[REUSED] RecoveryAction: {action.action_type.value} for Case {action.case_id}")

    # 6. AUDIT LOGS
    audit_logs_data = [
        # Log 1.1
        {
            "case_id": case1.id,
            "actor_type": ActorType.SYSTEM_RULE,
            "event_name": "CASE_DETECTED",
            "summary": "Failed UPI payment ingested from gateway webhook. Case created.",
            "state_before": None,
            "state_after": {"case_status": "DETECTED"},
            "agent_reasoning": None,
        },
        # Log 1.2
        {
            "case_id": case1.id,
            "actor_type": ActorType.AI_AGENT,
            "event_name": "DIAGNOSIS_COMPLETED",
            "summary": "Agent diagnosed transient bank outage; scheduled fallback payment link and WhatsApp nudge.",
            "state_before": {"case_status": "DETECTED"},
            "state_after": {
                "case_status": "IN_PROGRESS",
                "selected_strategy": "payment_link",
            },
            "agent_reasoning": (
                "Bank error indicates temporary network failure. "
                "Recommended generating an active Razorpay test payment link with 24-hour validity."
            ),
        },
        # Log 2.1
        {
            "case_id": case2.id,
            "actor_type": ActorType.AI_AGENT,
            "event_name": "PAYMENT_RECOVERED",
            "summary": "Smart retry transaction confirmed captured on gateway. Case marked RECOVERED.",
            "state_before": {"case_status": "IN_PROGRESS"},
            "state_after": {
                "case_status": "RECOVERED",
                "recovered_amount": "4999.00",
            },
            "agent_reasoning": "Retry attempt captured successfully. Total recovered revenue updated.",
        },
    ]

    for log_data in audit_logs_data:
        log = db.scalar(
            select(AuditLog).where(
                AuditLog.case_id == log_data["case_id"],
                AuditLog.event_name == log_data["event_name"],
                AuditLog.actor_type == log_data["actor_type"],
            )
        )
        if not log:
            log = AuditLog(
                case_id=log_data["case_id"],
                actor_type=log_data["actor_type"],
                event_name=log_data["event_name"],
                summary=log_data["summary"],
                state_before=log_data["state_before"],
                state_after=log_data["state_after"],
                agent_reasoning=log_data["agent_reasoning"],
            )
            db.add(log)
            db.flush()
            print(f"[CREATED] AuditLog: {log.event_name} by {log.actor_type.value}")
        else:
            log.summary = log_data["summary"]
            log.state_before = log_data["state_before"]
            log.state_after = log_data["state_after"]
            log.agent_reasoning = log_data["agent_reasoning"]
            db.flush()
            print(f"[REUSED] AuditLog: {log.event_name} by {log.actor_type.value}")


def verify_seed_data(db: Session) -> bool:
    """Verifies that all entities and relationships match seed specifications."""
    print("\n--- VERIFYING SEEDED RELATIONSHIP GRAPH ---")

    merchant = db.scalar(
        select(Merchant).where(Merchant.email == SEED_MERCHANT_EMAIL)
    )
    if not merchant:
        print("[FAIL] Merchant not found.")
        return False

    customers = db.scalars(
        select(Customer).where(Customer.merchant_id == merchant.id)
    ).all()
    transactions = db.scalars(
        select(Transaction).where(Transaction.merchant_id == merchant.id)
    ).all()
    cases = db.scalars(
        select(RecoveryCase).where(RecoveryCase.merchant_id == merchant.id)
    ).all()
    case_ids = [c.id for c in cases]
    actions = db.scalars(
        select(RecoveryAction).where(RecoveryAction.case_id.in_(case_ids))
    ).all()
    audit_logs = db.scalars(
        select(AuditLog).where(AuditLog.case_id.in_(case_ids))
    ).all()

    print(f"Merchant Count:         {1 if merchant else 0} (Expected: 1)")
    print(f"Customer Count:         {len(customers)} (Expected: 2)")
    print(f"Transaction Count:      {len(transactions)} (Expected: 2)")
    print(f"RecoveryCase Count:     {len(cases)} (Expected: 2)")
    print(f"RecoveryAction Count:   {len(actions)} (Expected: 3)")
    print(f"AuditLog Count:         {len(audit_logs)} (Expected: 3)")

    # Status verifications
    case1 = next((c for c in cases if c.selected_strategy == "payment_link"), None)
    case2 = next((c for c in cases if c.selected_strategy == "smart_retry"), None)

    case1_ok = case1 is not None and case1.status == CaseStatus.IN_PROGRESS
    case2_ok = case2 is not None and case2.status == CaseStatus.RECOVERED

    print(f"Case 1 (Payment Link) Status: {case1.status.value if case1 else 'None'} (Expected: IN_PROGRESS) -> {'PASS' if case1_ok else 'FAIL'}")
    print(f"Case 2 (Smart Retry)  Status: {case2.status.value if case2 else 'None'} (Expected: RECOVERED) -> {'PASS' if case2_ok else 'FAIL'}")

    all_ok = (
        len(customers) == 2
        and len(transactions) == 2
        and len(cases) == 2
        and len(actions) == 3
        and len(audit_logs) == 3
        and case1_ok
        and case2_ok
    )

    if all_ok:
        print("\n[SUCCESS] All seed data counts, statuses, and relationships verified!")
    else:
        print("\n[WARNING] Some verifications did not match expected counts.")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Seed RecoverX development database.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean existing test seed data before re-seeding.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        seed_data(db, clean=args.clean)
        db.commit()
        print("\n[COMMIT] Transaction committed successfully.")

        # Verification step
        verify_seed_data(db)
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seed operation failed: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
