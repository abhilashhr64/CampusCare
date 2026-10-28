"""CampusCare AI - Fee Management & Receipt API Router."""

from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any, List
from src.modules.fees.service import FeesService, PaymentInitiateRequest

router = APIRouter(prefix="/fees", tags=["Fees & Payments"])


@router.get("/dues")
def get_fee_dues(student_roll: str = "26CS01") -> Dict[str, Any]:
    """Retrieves active fee dues and ledger summary for a student."""
    return FeesService.get_student_dues(student_roll=student_roll)


@router.get("/receipts")
def get_fee_receipts(student_roll: str = "26CS01") -> List[Dict[str, Any]]:
    """Retrieves settled fee receipts for a student."""
    return FeesService.get_student_receipts(student_roll=student_roll)


@router.post("/pay")
def pay_fee_dues(payload: PaymentInitiateRequest) -> Dict[str, Any]:
    """Settles selected college fee dues via UPI, NetBanking, or Card and generates an official receipt."""
    try:
        return FeesService.pay_dues(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/receipts/{receipt_number}/download")
def download_fee_receipt(receipt_number: str, student_roll: str = "26CS01"):
    """Downloads or views the official, verifiable college fee receipt in HTML/print format."""
    html_content = FeesService.generate_html_receipt(receipt_number=receipt_number, student_roll=student_roll)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"inline; filename=Apex_Fee_Receipt_{receipt_number}.html",
        },
    )
