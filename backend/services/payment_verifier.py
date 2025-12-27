"""
Solana payment verification service
"""
import logging
from typing import Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PaymentVerification(BaseModel):
    """Payment verification result"""
    verified: bool
    amount_sol: Optional[float] = None
    signature: str
    error: Optional[str] = None


class SolanaPaymentVerifier:
    """Verify Solana transactions on-chain"""
    
    def __init__(self, rpc_url: str, expected_recipient: str, expected_amount_sol: float):
        self.rpc_url = rpc_url
        self.expected_recipient = expected_recipient
        self.expected_amount_sol = expected_amount_sol
        self.lamports_per_sol = 1_000_000_000
    
    async def verify_transaction(self, signature: str, sender: str) -> PaymentVerification:
        """
        Verify a transaction on Solana blockchain
        
        Args:
            signature: Transaction signature to verify
            sender: Expected sender wallet address
            
        Returns:
            PaymentVerification with verification result
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Get transaction details from Solana RPC
                response = await client.post(
                    self.rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getTransaction",
                        "params": [
                            signature,
                            {
                                "encoding": "json",
                                "maxSupportedTransactionVersion": 0,
                                "commitment": "confirmed"
                            }
                        ]
                    }
                )
                
                data = response.json()
                
                if "error" in data:
                    logger.error(f"RPC error: {data['error']}")
                    return PaymentVerification(
                        verified=False,
                        signature=signature,
                        error=f"Transaction not found: {data['error']['message']}"
                    )
                
                result = data.get("result")
                if not result:
                    return PaymentVerification(
                        verified=False,
                        signature=signature,
                        error="Transaction not found or not confirmed"
                    )
                
                # Extract transaction details
                meta = result.get("meta", {})
                transaction = result.get("transaction", {})
                message = transaction.get("message", {})
                
                # Check transaction succeeded
                if meta.get("err"):
                    return PaymentVerification(
                        verified=False,
                        signature=signature,
                        error=f"Transaction failed: {meta['err']}"
                    )
                
                # Get account keys and instructions
                account_keys = message.get("accountKeys", [])
                instructions = message.get("instructions", [])
                
                # Verify transfer instruction
                verified = False
                amount_lamports = 0
                
                for instruction in instructions:
                    # System Program transfer instruction
                    program_id_index = instruction.get("programIdIndex")
                    if program_id_index is not None and account_keys[program_id_index] == "11111111111111111111111111111111":
                        accounts = instruction.get("accounts", [])
                        if len(accounts) >= 2:
                            from_account = account_keys[accounts[0]]
                            to_account = account_keys[accounts[1]]
                            
                            # Verify sender and recipient
                            if from_account == sender and to_account == self.expected_recipient:
                                # Extract amount from instruction data
                                data_bytes = instruction.get("data", "")
                                if data_bytes:
                                    # Decode base58 instruction data (first byte is instruction type, next 8 bytes are amount)
                                    # For now, get from postBalances difference
                                    pre_balances = meta.get("preBalances", [])
                                    post_balances = meta.get("postBalances", [])
                                    
                                    if len(pre_balances) >= 2 and len(post_balances) >= 2:
                                        amount_lamports = pre_balances[0] - post_balances[0]
                                        verified = True
                
                if not verified:
                    return PaymentVerification(
                        verified=False,
                        signature=signature,
                        error="Payment not found or incorrect recipient/sender"
                    )
                
                # Verify amount
                amount_sol = amount_lamports / self.lamports_per_sol
                expected_min = self.expected_amount_sol * 0.99  # Allow 1% tolerance for fees
                
                if amount_sol < expected_min:
                    return PaymentVerification(
                        verified=False,
                        signature=signature,
                        amount_sol=amount_sol,
                        error=f"Insufficient payment: {amount_sol} SOL (expected {self.expected_amount_sol})"
                    )
                
                logger.info(f"Payment verified: {amount_sol} SOL from {sender} (tx: {signature[:8]}...)")
                
                return PaymentVerification(
                    verified=True,
                    signature=signature,
                    amount_sol=amount_sol
                )
                
        except Exception as e:
            logger.error(f"Payment verification error: {e}", exc_info=True)
            return PaymentVerification(
                verified=False,
                signature=signature,
                error=f"Verification failed: {str(e)}"
            )

        except httpx.ReadTimeout:
            logger.error(f"Timeout verifying transaction {signature}")
            return PaymentVerification(
                verified=False,
                signature=signature,
                error="Transaction verification timed out. Please try again."
            )
