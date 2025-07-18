import datetime

class DateUtils:
    @staticmethod
    def get_current_date(format: str = '%Y-%m-%dT%H:%M:%S+05:30') -> str:
        # Create IST timezone once
        ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        ist_time = datetime.datetime.now(ist_timezone)
        return ist_time.strftime(format)
    
    @staticmethod
    def get_date_by_time_range(time_range: str, format: str = '%Y-%m-%dT%H:%M:%S+05:30') -> str:
        # Create IST timezone once
        ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        # Calculate date directly in IST timezone
        ist_date = datetime.datetime.now(ist_timezone) - datetime.timedelta(days=int(time_range))
        return ist_date.strftime(format)

    @staticmethod
    def get_end_date_by_start_date_and_time_range(start_date: str, time_range: str, format: str = '%Y-%m-%dT%H:%M:%S+05:30') -> str:
        # Create IST timezone once
        ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        # Calculate date directly in IST timezone
        ist_date = datetime.datetime.strptime(start_date, format) + datetime.timedelta(days=int(time_range))
        return ist_date.strftime(format)