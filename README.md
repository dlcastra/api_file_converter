# File Converter API

## Description

This API allows for file format conversion using LibreOffice & UNO or custom scripts. Additionally, it provides a feature to search for sentences in files based on given keywords.

File conversion is performed by modifying the file's byte content. Sentence searching is done by downloading the file and extracting the text.

## Services and Technologies

The following technologies were used to implement this API:

- Python 3.12
- FastAPI
- LibreOffice & UNO
- Docker
- Docker Compose
- AWS S3, SQS, IAM
- Google Translate API

## How It Works

This API supports both direct HTTP requests and requests via Amazon SQS task queues. All requests are processed asynchronously.

### Direct Request Flow:
1. The endpoint receives the request and forwards the data to the handler.
2. The handler fetches the file's byte code or the full file, depending on the endpoint.
3. The data is passed to an internal file processing service.
4. The service processes the file and returns the result to the handler.
5. The handler sends the response back to the endpoint.
6. The endpoint forwards the result to the specified callback URL.

### SQS Queue Request Flow:
1. A function inside the service checks whether there is data in the queue.
2. If data is found, the function retrieves it and attempts to determine the appropriate handler.
3. If a valid handler is found, the data is passed to it; otherwise, the message is removed from the queue.
4. The handler processes the data and returns the result.
5. The result is sent to the callback URL.

## API Endpoints

### Convert File Endpoint
- **URL:** `/api/v1/converter/convert-file`
- **Method:** `POST`
- **Supported Formats:** `doc, docx, txt, pdf, png, jpg, jpeg`
- **Request Body Example:**
  ```json
  {
      "s3_key": "some_file.txt",
      "format_from": "txt",
      "format_to": "pdf",
      "callback_url": "https://webhook/mywebhook"
  }
  ```

### Parse File Endpoint
- **URL:** `/api/v1/parser/parse-file`
- **Method:** `POST`
- **Supported Formats:** `txt, docx, pdf`
- **Request Body Example:**
  ```json
  {
      "s3_key": "some_file.txt",
      "keywords": ["some", "keywords"],
      "callback_url": "https://webhook/mywebhook"
  }
  ```

## Example API Requests

### Using cURL

#### Convert File Request
```sh
curl -X POST "https://api.example.com/api/v1/converter/convert-file" \
     -H "Content-Type: application/json" \
     -d '{
           "s3_key": "some_file.txt",
           "format_from": "txt",
           "format_to": "pdf",
           "callback_url": "https://webhook/mywebhook"
         }'
```

#### Parse File Request
```sh
curl -X POST "https://api.example.com/api/v1/parser/parse-file" \
     -H "Content-Type: application/json" \
     -d '{
           "s3_key": "some_file.txt",
           "keywords": ["some", "keywords"],
           "callback_url": "https://webhook/mywebhook"
         }'
```

## Example API Responses

### Success Response
- **Convert File Response:**
```json
{
  "file_url": "https://your-bucket.s3.eu-north-1.amazonaws.com/some_file.pdf",
  "new_s3_key": "some_file.pdf",
  "status": "success"
}
```
- **Parse File Response:**
```json
{
  "count": 1,
  "sentences": ["Some sentence with the keyword."],
  "status": "success"
}
```

### Error Response
```json
{
    "status": "error",
    "message": "Invalid file format"
}
```

## How to Run the API

### Running with Docker
1. Clone the repository:
   ```sh
   git clone https://github.com/dlcastra/api_file_converter.git
   ```
2. Configure environment variables in the `.env` file (use `.env.ex` as an example).
3. Build and start the containers:
   ```sh
   docker-compose up --build
   ```

### Running Locally
1. Clone the repository:
   ```sh
   git clone https://github.com/dlcastra/api_file_converter.git
   ```
2. Configure environment variables in the `.env` file (use `.env.ex` as an example).
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Start the application:
   ```sh
   uvicorn application:app --reload --port 8000
   ```

## Error Handling
- If the file is not found in S3, an appropriate error response is returned.
- If the file format is not supported, the request is rejected with a descriptive error message.
- If an unexpected error occurs, a generic error response is sent, and logs are generated for debugging.
