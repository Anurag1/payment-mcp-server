import requests
import json
from config.settings import settings
import uuid
from utils.authentication_utils import AuthenticationUtils

class SettlementService:
    def __init__(self, mid: str, client_id: str, client_secret: str):
        self.mid = mid
        self.base_url = settings.PAYTM_BASE_URL
        self.client_id = client_id
        self.client_secret = client_secret



    def get_settlement_summary(
        self,
        page_num: int = 1,
        page_size: int = 10,
        start_date: str = None,
        end_date: str = None,
        payout_id: str = None
    ) -> str:
        """
        Fetches the settlement summary for the merchant for a given date range or payout ID either one of them is required.
        Args:
            page_num (int): Page number
            page_size (int): Page size (max 50)
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str, optional): End date (YYYY-MM-DD) Maximum Date Range between Start and End date supported is 1 week
            payout_id (str, optional): Payout ID
        Returns:
            str: Formatted settlement summary or error message
        """
        api_path = "/merchant-settlement/SettlementSummary"
        url = self.base_url + api_path
        body = {
            "mid": self.mid,
            "pageNum": page_num,
            "pageSize": page_size
        }

        if payout_id:
            body["payoutId"] = payout_id

        if start_date:
            body["startDate"] = start_date

        if end_date:
            body["endDate"] = end_date

        payload = self.get_payout_details(body)

        headers = self.get_headers(payload)
        settlement_summary = self.settlement_summary_api(url, payload, headers)
        return settlement_summary
        

    def get_payout_details(self,body: dict) -> str:
        payload = {
            "request": {
                "head": {"reqMsgId": AuthenticationUtils.uuid_generator(self.mid)},
                "body": body
            }
        }
        return payload
        
    def get_headers(self, payload: dict) -> dict:
        return {
            "Content-Type": "application/json",
            "clientId": self.client_id,
            "Authorization": f"Bearer {AuthenticationUtils.generate_token(self.client_secret, payload)}",
            "x-api-key": self.client_id
        }
    

    def settlement_summary_api(self, url: str, payload: dict, headers: dict) -> str:
        try:
            response = requests.post(url, json=payload, headers=headers)
            if not response.ok:
                return f"API request failed with status code: {response.status_code}"
            try:
                data = response.json()
            except json.JSONDecodeError:
                return "Error: Invalid JSON response from server"
            # Check for result status
            if data['response']['body']['resultCode'] != 'SUCCESS':
                return f"Error from response: {data['response']} and the request is {payload}"
            return data['response']
        except Exception as e:
            return f"Error fetching settlement summary: {str(e)}"
        
    def get_settlement_details_by_order_id(self, order_id: str, transaction_date: str) -> str:
        """
        Fetches the settlement details for a specific order on a given transaction date.
        
        Args:
            order_id (str): The ID of the order to fetch settlement details for 
            transaction_date (str): The date of the transaction in ISO format (YYYY-MM-DD)
        Returns:
            str: The settlement details for the order
            str: Error message in case of failure
        """
        api_path = "/merchant-settlement/SettlementTransactionDetail"    
        url = self.base_url + api_path
        payload = {
            "mid": self.mid,
            "orderId": order_id,
            "transactionDate": transaction_date
        }   
        payload = self.get_payout_details(payload)
        headers = self.get_headers(payload)
        settlement_order_details = self.get_settlement_details_by_order_id_api(url, payload, headers)
        return settlement_order_details
    def get_settlement_details_by_transaction_id(self, transaction_id: str) -> str:
        """
        Get the settlement details for a specific transaction.
        """
        api_path = "/merchant-settlement/SettlementOrderDetail"
        url = self.base_url + api_path  
        payload = {
            "mid": self.mid,
            "transactionId": transaction_id
        }
        payload = self.get_payout_details(payload)
        headers = self.get_headers(payload)
        settlement_details = self.get_settlement_details_by_transaction_id_api(url, payload, headers)
        return settlement_details
    
   
    def settlement_detail_api(self, url: str, payload: dict, headers: dict) -> str:
        try:
            response = requests.post(url, json=payload, headers=headers)
            if not response.ok:
                return f"API request failed with status code: {response.status_code}"
            data = response.json()
            result_body = data['response']['body']
            if not result_body:
                return f"No settlement transaction details found. Raw response: {data}"
            settlement_summary_list = result_body.get('settlementSummaryList',[])
            if not settlement_summary_list:
                return "No settlement transaction details found."
            return settlement_summary_list
        except Exception as e:
            return f"Error fetching settlement transaction details: {str(e)}"
            
    def get_settlement_detail(
        self,
        page_num: int = 1,
        page_size: int = 10,
        start_date: str = None,
        end_date: str = None,
        payout_id: str = None
    ) -> str:
        """
        Fetches the settlement details transactional wise with the merchant for a given date range or payout ID either one of them is required.
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str, optional): End date (YYYY-MM-DD) Maximum Date Range between Start and End date supported is 1 week
            payout_id (str, optional): Payout ID
            page_num (int): Page number
            page_size (int): Page size (max 50)
        Returns:
            str: Formatted settlement summary or error message
        """
        api_path = "/merchant-settlement/SettlementDetail"
        url = self.base_url + api_path
        payload = {
            "mid": self.mid,
            "pageNum": page_num,
            "pageSize": page_size
        }
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        if payout_id:
            payload["payoutId"] = payout_id
        payload = self.get_payout_details(payload)
        headers = self.get_headers(payload)
        settlement_detail = self.settlement_detail_api(url, payload, headers)
        return settlement_detail
    
    def get_settlement_details_by_transaction_id_api(self, url: str, payload: dict, headers: dict) -> str:
        try:
            response = requests.post(url, json=payload, headers=headers)
            if not response.ok:
                return f"API request failed with status code: {response.status_code}"
            data = response.json()
            result_body = data['response']['body']
            if not result_body:
                return f"No settlement transaction details found. Raw response: {data}"   
            settlement_detail = (
                f"Transaction ID: {result_body.get('transactionId', 'N/A')}\n"
                f"orderId: {result_body.get('orderId', 'N/A')}\n"
                f"transactionDate: {result_body.get('transactionDate', 'N/A')}\n"
                f"transactionAmount: {result_body.get('amount', 'N/A')}\n"
                f"transactionStatus: {result_body.get('status', 'N/A')}\n"
                f"transactionType: {result_body.get('transactionType', 'N/A')}\n"
                f"payoutId: {result_body.get('payoutId', 'N/A')}\n"
                f"settledDate: {result_body.get('settledDate', 'N/A')}\n"
                f"settlementAmount: {result_body.get('settledAmount', 'N/A')}\n"
                f"extSerialNo: {result_body.get('extSerialNo', 'N/A')}\n"
                f"payoutDate: {result_body.get('payoutDate', 'N/A')}\n"
                f"utr: {result_body.get('utrNo', 'N/A')}\n"
            )
            return str(settlement_detail)    
        except Exception as e:
            return f"Error fetching settlement transaction details: {str(e)}"
    

    def get_settlement_details_by_order_id_api(self, url: str, payload: dict, headers: dict) -> str:
        try:
            response = requests.post(url, json=payload, headers=headers)
            if not response.ok:
                return f"API request failed with status code: {response.status_code}"
            data = response.json()
            result_body = data['response']['body']
            if not result_body:
                return f"No settlement transaction details found. Raw response: {data}"  
            
            # Handle the list of orders properly
            settlement_details = []
            for order in result_body['orders']:
                settlement_detail = (
                    f"Order ID: {order.get('orderId', 'N/A')}\n"
                    f"Transaction ID: {order.get('transactionId', 'N/A')}\n"
                    f"Transaction Date: {order.get('transactionDate', 'N/A')}\n"
                    f"Transaction Amount: {order.get('amount', 'N/A')}\n"
                    f"Transaction Status: {order.get('status', 'N/A')}\n"
                    f"Transaction Type: {order.get('transactionType', 'N/A')}\n"
                    f"Payout ID: {order.get('payoutId', 'N/A')}\n"
                    f"Settled Date: {order.get('settledDate', 'N/A')}\n"
                    f"Settlement Amount: {order.get('settledAmount', 'N/A')}\n"
                    f"Ext Serial No: {order.get('extSerialNo', 'N/A')}\n"
                    f"Payout Date: {order.get('payoutDate', 'N/A')}\n"
                    f"UTR: {order.get('utrNo', 'N/A')}\n")
                settlement_details.append(settlement_detail)
            
            # Join all settlement details with separators
            return "\n" + "="*50 + "\n".join(settlement_details) + "="*50 + "\n"
            

        except Exception as e:
            return f"Error fetching settlement transaction details: {str(e)}"
            