#!/bin/bash

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and rerun this script."
    exit 1
fi

# Check for pip3
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Attempting to install pip3..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Check for PyJWT
if ! python3 -c "import jwt" &> /dev/null; then
    echo "PyJWT not found. Installing PyJWT..."
    pip3 install --user PyJWT
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    echo "jq not found. Installing jq using Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is not installed. Please install Homebrew and rerun this script."
        exit 1
    fi
    brew install jq
fi

# Generate JWT token using Python
TOKEN=$(python3 -c "
import jwt, datetime
SECRET_KEY = '<SECRET_KEY>'
ALGORITHM = 'HS256'
payload = {
    'username': '<USERNAME>',
    'merchant_id': '<MERCHANT_ID>',
    'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
}
token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(token)
")

printf "\033[1mGenerated token:\033[0m %s\n" "$TOKEN"