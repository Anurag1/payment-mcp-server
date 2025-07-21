import sys
import os
import logging
from typing import Optional, List

from mcp.server.fastmcp import FastMCP
from services.payment_service import PaymentService
from services.refund_service import RefundService
from services.order_list_service import OrderListService
from config.settings import settings
from utils.models import PaymentLink, Transaction
from utils.system_utils import DateUtils
from services.settlement_service import SettlementService
from config.constants import Format

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("paytm-mcp-server")

# Initialize services
try:
    payment_service = PaymentService(settings.PAYTM_KEY_SECRET,settings.PAYTM_MID)
    refund_service = RefundService(settings.PAYTM_KEY_SECRET,settings.PAYTM_MID)
    order_list_service = OrderListService(settings.PAYTM_KEY_SECRET,settings.PAYTM_MID)
    settlement_service = SettlementService(settings.PAYTM_MID,settings.PAYTM_CLIENT_ID,settings.PAYTM_CLIENT_SECRET)
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    sys.exit(1)

def main():
    mcp.run()

# Tool: Create Payment Link
@mcp.tool()
def create_payment_link(
    recipient_name: str,
    purpose: str,
    customer_email: str = None,
    customer_mobile: str = None,
    amount: str = None,
) -> str:
    """
    Create a new payment link for receiving payments.

    This operation generates a unique payment link that can be shared with customers
    for accepting payments. The link can be customized with recipient details,
    purpose, customer details and amount.

    Required Parameters:
        recipient_name (str): Name of the person or entity receiving the payment
        purpose (str): Description or reason for the payment
        customer_email (str): Email address of the customer
        customer_mobile (str): Mobile number of the customer
        Either customer_email or customer_mobile must be provided if else please ask from the user

    Optional Parameters:
        amount (float): Fixed amount for the payment

    Note:
        - Amount can be left optional for customer to decide
        - Generated link will be valid according to system's expiry settings
        - Please ask all the required fields from the user don't assume any fields
    
    IMPORTANT NOTE:
        - if user is not providing customer_email or customer_mobile, please ask for the same don't call any tool before asking for the same
        """
    
    try:
        return payment_service.create_payment_link(
            recipient_name=recipient_name,
            purpose=purpose,
            customer_email=customer_email,
            customer_mobile=customer_mobile,
            amount=amount
        )
    except Exception as e:
        logger.error(f"Failed to create payment link: {str(e)}")
        return str(e)

# Tool: Fetch All Payment Links
@mcp.tool()
def fetch_payment_links() -> str:
    """
    Retrieve all payment links created by the merchant.

    This operation returns a comprehensive list of all payment links created,
    including both active and expired links. Each link entry contains details
    such as:
        - Link ID
        - Link Name
        - Short URL
        - Status
        - Creation Date
        - Expiry Date

    Returns:
        List[PaymentLink]: A list of PaymentLink objects containing link details
        str: Error message in case of failure
    """
    try:
        links: List[PaymentLink] = payment_service.fetch_payment_links()
        if not links:
            return "No payment links found."
        return links
    except Exception as e:
        logger.error(f"Failed to fetch payment links: {str(e)}")
        return str(e)

# Tool: Fetch Transactions for a Specific Link
@mcp.tool()
def fetch_transactions_for_link(link_id: str) -> str:
    """
    Retrieve all transactions associated with a specific payment link.

    This operation provides detailed transaction history for a given payment link,
    including successful and failed transactions.

    Parameters:
        link_id (str): Unique identifier of the payment link

    Returns:
        List[Transaction]: List of transactions containing details such as:
            - Transaction ID
            - Order ID
            - Amount
            - Status
            - Completion Time
            - Customer Contact Information
        str: Error message in case of failure
    """
    try:
        transactions: List[Transaction] = payment_service.fetch_transactions_for_link(link_id)
        if not transactions:
            return f"No transactions found for link ID {link_id}."
    
        return transactions
    except Exception as e:
        logger.error(f"Failed to fetch transactions: {str(e)}")
        return str(e)

# Tool: Initiate Refund
@mcp.tool()
def initiate_refund(order_id: str, refund_reference_id: str, txn_id: str, refund_amount: float) -> str:
    """
    Initiate a refund for a specific transaction.

    This operation allows the merchant to initiate a refund for a previously
    completed transaction. The refund can be initiated for a specific amount,
    and the refund reference ID will be used to track the refund request.

    IMPORTANT NOTE:
        - if user is not providing order_id, please ask for the same don't call any tool before asking for the same
        - if user is not providing txn_id, please ask for the same don't call any tool before asking for the same
        - if user is not providing refund_reference_id, please ask for the same don't call any tool before asking for the same
        - if user is not providing refund_amount, please ask for the same don't call any tool before asking for the same
        

    Parameters:
        order_id (str): Original order ID of the transaction
        refund_reference_id (str): Unique refund reference ID (max 50 chars)
        txn_id (str): Original Paytm transaction ID
        refund_amount (float): Amount to be refunded (must be <= original transaction amount)

    Returns:
        str: Response message indicating success or failure of refund initiation along with the Refund Status, Message and Code of the refund
    """
    try:
        response =  refund_service.initiate_refund(order_id, refund_reference_id, txn_id, refund_amount)
        return response

    except Exception as e:
        logger.error(f"Failed to initiate refund: {str(e)}")
        return str(e)


# Tool: Check Refund Status
@mcp.tool()
def check_refund_status(order_id: str, refund_reference_id: str) -> str:
    """
    Check the status of a previously initiated refund.

    This operation allows the merchant to check the status of a previously
    initiated refund. The refund status can be checked for a specific order
    and refund reference ID.

    Parameters:
    order_id (str): Original order ID of the transaction
    refund_reference_id (str): Refund reference ID used during refund initiation

    Returns:
    str: Current status of the refund request
    str: Error message in case of failure
    """
    try:
        return refund_service.check_refund_status(order_id, refund_reference_id)
    except Exception as e:
        logger.error(f"Failed to check refund status: {str(e)}")
        return str(e)
    


    
# Tool: Fetch Refund List
@mcp.tool()
def fetch_refund_list(
    is_sort: bool = True, 
    page_num: int = 1, 
    page_size: int = 50, 
    time_range: str = "7",
    start_date: str = None,
    end_date: str = None
    ) -> str:
    """
    Fetch the list of refunds for the merchant within a date range of 30 days and never assume start_date and end_date.
    
    This operation allows the merchant to retrieve a list of refunds that have been
    initiated within a specified date range. The list can be sorted by date and
    paginated to handle large datasets.

    Parameters:
    start_date (str): Start date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
    end_date (str): End date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
    is_sort (bool): Whether to sort the list by date
    page_num (int): The page number to retrieve
    page_size (int): The number of refunds per page
    time_range (str): Time range in days (default: 7)

    Returns:
    str: The list of refunds along with the Order ID, Refund ID, Ref ID, Txn Amount, Refund Amount, Refund Time of the refund
    str: Error message in case of failure
    """
    try:
        if not (start_date and end_date):
            start_date = DateUtils.get_date_by_time_range(time_range)
            end_date = DateUtils.get_current_date()
        return refund_service.fetch_refund_list(start_date, end_date, is_sort, page_num, page_size)
    except Exception as e:
        logger.error(f"Failed to fetch refund list from paytm mcp: {str(e)}")
        return str(e)
    

# Tool: Fetch Order List
@mcp.tool()
def fetch_order_list(
    order_search_type: str = "TRANSACTION",
    order_search_status: str = "SUCCESS",
    page_number: int = 1,
    page_size: int = 50,
    from_date: str = None,
    to_date: str = None,
    time_range: str = "7",
) -> str:
    """
    Fetch the list of orders from Paytm within a date range of 30 days and never assume from_date and to_date.

    This operation allows the merchant to retrieve a list of orders that have been
    created within a specified date range. The list can be filtered by order_search_status, order_search_type and
    paginated to handle large datasets.

    Parameters:
        from_date (str): Start date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
        to_date (str): End date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
        order_search_type (str): Type of order search (default: TRANSACTION)
        order_search_status (str, optional): Status of orders to search for
        page_number (int): Page number for pagination (default: 1)
        page_size (int): Number of records per page (default: 50)
        time_range (str): Time range in days (default: 7)
        
        - from_date and to_date or time_range SHOULD NOT be more than 30 days apart.Don't accept more than 30 days request from the user   

    Returns:
        str: The list of orders with their details
        str: Error message in case of failure
    """
    if not (from_date and to_date):
        from_date = DateUtils.get_date_by_time_range(time_range)
        to_date = DateUtils.get_current_date()
    try:
        return order_list_service.fetch_order_list(
            from_date=from_date,
            to_date=to_date,
            order_search_type=order_search_type,
            order_search_status=order_search_status,
            page_number=page_number,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Failed to fetch order list: {str(e)}")
        return str(e)
@mcp.tool()
def get_settlement_order_details(order_id: str,transaction_date: str) -> str:
    """
    Get the settlement details for a specific order.

    This operation allows the merchant to retrieve the settlement details for a
    specific order.

    Parameters:
        order_id (str): The order ID to retrieve settlement details for
        transaction_date (str): The date of the transaction in ISO format (YYYY-MM-DD) please ask from the user don't generate any random date
        
    Returns:    
        str: The settlement details for the order
        str: Error message in case of failure

    IMPORTANT INSTRUCTIONS FOR ID HANDLING:
        - Order ID format: 20xxxxxxxxxxxx098 
        - If user provides an ID without clearly stating it's an "order ID", you MUST ask them to clarify what type of ID they are providing
        - Do NOT assume any ID is an order ID unless the user explicitly mentions "order ID" or the ID clearly matches the order ID format
        - If the ID doesn't match the expected order ID format, ask the user to confirm if this is indeed an order ID
        - Only proceed with this function when you're certain the provided ID is an order ID
        
    """
    try:
        return settlement_service.get_settlement_details_by_order_id(order_id,transaction_date)
    except Exception as e:
        logger.error(f"Failed to get settlement order details: {str(e)}")
        return str(e)   
    
@mcp.tool()
def get_settlement_transaction_details(transaction_id: str) -> str:
    """
    Retrieve settlement details for a specific transaction by transaction ID.

    This operation fetches comprehensive settlement information for a given transaction ID,
    including settlement amounts, dates, payout details, and transaction status.

    Parameters:
        transaction_id (str): The transaction ID to retrieve settlement details for

    Returns:
        str: Formatted settlement details including transaction ID, order ID, settlement amount,
             payout ID, settlement date, UTR number, and transaction status
        
    IMPORTANT INSTRUCTIONS FOR ID HANDLING:
        - Transaction ID format: 202xxxxxxxxxxxxxxxxxxxxx1066   
        - If user provides an ID without clearly stating it's a "transaction ID", you MUST ask them to clarify what type of ID they are providing
        - Do NOT assume any ID is a transaction ID unless the user explicitly mentions "transaction ID" or the ID clearly matches the transaction ID format
        - If the ID doesn't match the expected transaction ID format, ask the user to confirm if this is indeed a transaction ID
        - Only proceed with this function when you're certain the provided ID is a transaction ID
        
    """
    try:
        return settlement_service.get_settlement_details_by_transaction_id(transaction_id)
    except Exception as e:
        logger.error(f"Failed to get settlement transaction details: {str(e)}")
        return str(e)
@mcp.tool()
def get_settlement_summary(
        page_num: int = 1,
        page_size: int = 10,
        start_date: str = None,
        end_date: str = None,
        payout_id: str = None,
        time_range: str = "7"
        ) -> str:
    """
    Fetches the settlement summary for the merchant for a given date range or payout ID either one of them is required.
    
    Args:
            page_num (int): Page number
            page_size (int): Page size (max 50)
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str, optional): End date (YYYY-MM-DD) Maximum Date Range between Start and End date supported is 1 week
                                    - do not assume end date if start date is provided
                                    - start date and end date should not be more than 7 days apart 
            payout_id (str, optional): Payout ID for specific payout settlement summary
            time_range (str,optional): The time range in days to retrieve settlement summary
                                    - time range should not be more than 7 days
                                    - default time range is 7 days

            - start_date and end_date or time_range SHOULD NOT be more than 30 days apart.Don't accept more than 30 days request from the user  
            
    Returns:
        str: Formatted settlement summary or error message

    IMPORTANT INSTRUCTIONS :
        - This tool should be used when the user asking for settlement 
        
    IMPORTANT INSTRUCTIONS FOR ID HANDLING:
        - If user provides an ID without clearly stating it's a "payout ID", you MUST ask them to clarify what type of ID they are providing
        - Do NOT assume any ID is a payout ID unless the user explicitly mentions "payout ID"
        - Only use the payout_id parameter when you're certain the provided ID is a payout ID
        - If no payout ID is provided, use date range or time_range instead
        
    """
    try:
        format = Format.BASIC_DATE_FORMAT
        if not payout_id:
            if (not end_date) and start_date:
                end_date = DateUtils.get_end_date_by_start_date_and_time_range(start_date,time_range,format)
            elif not (end_date and start_date):
                start_date = DateUtils.get_date_by_time_range(time_range,format)
                end_date = DateUtils.get_current_date(format)
        return settlement_service.get_settlement_summary(page_num,page_size,start_date,end_date,payout_id)
    except Exception as e:
        logger.error(f"Failed to get settlement summary: {str(e)}")
        return str(e)

@mcp.tool()
def get_settlement_detail(
    start_date: str = None,
    end_date: str = None,
    page_num: int = 1,
    page_size: int = 10,
    payout_id: str = None,
    time_range: str = "7"
    ) -> str:
    """
    This tool helps the merchant to retrieve the settlement details in transactional basis.

    Parameters:
        start_date (str,optional): The start date of the transaction in YYYY-MM-DD format
        end_date (str,optional): The end date of the transaction in YYYY-MM-DD format
                        - do not assume end date if start date is provided
                        - start date and end date should not be more than 7 days apart 
        page_num (int): The page number to retrieve
        page_size (int): The number of transactions per page
        payout_id (str,optional): The payout ID to retrieve settlement details for specific payout
        time_range (str,optional): The time range in days to retrieve settlement details
                        - time range should not be more than 7 days

    IMPORTANT INSTRUCTIONS :
        - This tool should be used when the user asking for settlement details in transactional basis

    IMPORTANT INSTRUCTIONS FOR ID HANDLING:
        - If user provides an ID without clearly stating it's a "payout ID", you MUST ask them to clarify what type of ID they are providing
        - Do NOT assume any ID is a payout ID unless the user explicitly mentions "payout ID"
        - Only use the payout_id parameter when you're certain the provided ID is a payout ID
        - If no payout ID is provided, use date range or time_range instead

    """
    try:
        format = Format.BASIC_DATE_FORMAT
        if not payout_id:
            if (not end_date) and start_date:
                end_date = DateUtils.get_end_date_by_start_date_and_time_range(start_date,time_range,format)
            elif not (end_date and start_date):
                start_date = DateUtils.get_date_by_time_range(time_range,format)
                end_date = DateUtils.get_current_date(format)

        return settlement_service.get_settlement_detail(page_num,page_size,start_date,end_date,payout_id)
    except Exception as e:
        logger.error(f"Failed to get settlement details: {str(e)}")
        return str(e)

if __name__ == "__main__":
    main()
