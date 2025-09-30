# Excuse Email Draft Tool

A complete web application for generating professional excuse emails using Databricks Model Serving LLM. Built with FastAPI backend and React frontend, designed to work locally and deploy seamlessly to Databricks Apps.

## Features

- **AI-Powered Email Generation**: Uses Databricks Model Serving LLM to generate contextually appropriate excuse emails
- **Customizable Parameters**: Choose from 6 categories, 3 tones, and 5 seriousness levels
- **Modern UI**: Clean, responsive design built with React and Tailwind CSS
- **Professional Output**: Generates both subject lines and email bodies with proper formatting
- **Copy to Clipboard**: One-click copying of generated emails
- **Comprehensive Error Handling**: Graceful error handling with user-friendly messages
- **Health Monitoring**: Multiple health check endpoints for monitoring
- **Databricks Apps Ready**: Optimized for deployment to Databricks Apps platform

## Project Structure

```
excuse-gen-app/
├── app.yaml                    # Databricks Apps configuration
├── requirements.txt            # Python dependencies
├── env.example                 # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── src/
│   └── app.py                 # FastAPI backend application
└── public/
    └── index.html             # React frontend (single-file app)
```

## Quick Start

### Local Development

1. **Clone and Setup**:
   ```bash
   cd excuse-gen-app
   pip install -r requirements.txt
   cp env.example .env
   ```

2. **Configure Environment**:
   Edit `.env` file with your Databricks credentials:
   ```env
   DATABRICKS_API_TOKEN=your_databricks_personal_access_token
   DATABRICKS_ENDPOINT_URL=https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations
   ```

3. **Run the Application**:
   ```bash
   python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the Application**:
   Open your browser and navigate to: `http://localhost:8000`

### Databricks Apps Deployment

1. **Prerequisites**:
   - Databricks workspace with Apps enabled
   - Databricks Model Serving endpoint accessible
   - App secret configured with key `databricks_token`

2. **Deploy**:
   ```bash
   databricks apps deploy excuse-gen-app --source-code-path /path/to/excuse-gen-app
   ```

3. **Access**:
   The app will be available at the URL provided by Databricks Apps

## API Endpoints

### Main Endpoint
- `POST /api/generate-excuse` - Generate excuse email

### Health & Monitoring
- `GET /health` - Health check
- `GET /healthz` - Alternative health check
- `GET /ready` - Readiness check
- `GET /ping` - Ping endpoint
- `GET /metrics` - Prometheus metrics
- `GET /debug` - Environment debugging

### Frontend
- `GET /` - Serve React application

## Usage

### Web Interface

1. **Select Category**: Choose from Running Late, Missed Meeting, Deadline, WFH/OOO, Social, or Travel
2. **Choose Tone**: Select Sincere, Playful, or Corporate
3. **Set Seriousness**: Use the slider from 1 (very silly) to 5 (serious)
4. **Fill Details**: Enter recipient name, sender name, and ETA/when information
5. **Generate**: Click "Generate Email" to create your excuse
6. **Copy**: Use "Copy to Clipboard" to copy the generated email

### API Usage

```bash
curl -X POST "http://localhost:8000/api/generate-excuse" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Running Late",
    "tone": "Sincere",
    "seriousness": 3,
    "recipient_name": "Alex",
    "sender_name": "Mona",
    "eta_when": "15 minutes"
  }'
```

Response:
```json
{
  "subject": "Running Late - ETA 15 minutes",
  "body": "Dear Alex,\n\nI wanted to let you know that I'm running about 15 minutes behind schedule...\n\nBest regards,\nMona",
  "success": true,
  "error": null
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABRICKS_API_TOKEN` | Databricks personal access token | Required |
| `DATABRICKS_ENDPOINT_URL` | Model serving endpoint URL | Required |
| `PORT` | Server port | 8000 |
| `HOST` | Server host | 0.0.0.0 |

### Databricks Apps Configuration

The `app.yaml` file configures the deployment:

```yaml
command: [
  "uvicorn",
  "src.app:app",
  "--host", "0.0.0.0",
  "--port", "8000"
]

env:
  - name: 'DATABRICKS_API_TOKEN'
    valueFrom: databricks_token  # References App secret
  - name: 'DATABRICKS_ENDPOINT_URL'
    value: "https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations"
  - name: 'PORT'
    value: "8000"
  - name: 'HOST'
    value: "0.0.0.0"
```

## Technical Details

### Backend (FastAPI)

- **Framework**: FastAPI with async support
- **CORS**: Enabled for React frontend
- **Logging**: Comprehensive request/response logging
- **Error Handling**: Graceful error handling with meaningful messages
- **Static Files**: Serves React app from `/public/index.html`
- **Health Checks**: Multiple endpoints for monitoring

### Frontend (React)

- **Framework**: React 18 with hooks
- **Styling**: Tailwind CSS via CDN
- **State Management**: React hooks for form and UI state
- **API Integration**: Fetch API for backend communication
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Accessibility**: Proper labels and keyboard navigation

### LLM Integration

- **Model**: Databricks Model Serving LLM
- **Prompt Engineering**: Structured prompts for consistent output
- **Response Parsing**: Handles multiple response formats
- **Error Handling**: Robust error handling for API failures
- **Timeout**: 30-second timeout for API calls

## Troubleshooting

### Common Issues

1. **"Databricks API token not configured"**:
   - Ensure `DATABRICKS_API_TOKEN` is set in your environment
   - For Databricks Apps, verify the `databricks_token` secret is configured

2. **"Request timeout to Databricks API"**:
   - Check your network connection
   - Verify the endpoint URL is correct and accessible
   - The API has a 30-second timeout

3. **"Frontend not found"**:
   - Ensure `public/index.html` exists
   - Check file permissions
   - Verify the public directory is accessible

4. **Port 8000 already in use**:
   - Change the PORT environment variable
   - Kill the process using port 8000
   - Use a different port for local development

### Debugging

- Use `/debug` endpoint to check environment configuration
- Check application logs for detailed error information
- Verify Databricks Model Serving endpoint is accessible
- Test API endpoints directly using curl or Postman

## Development

### Adding New Categories

1. Update the `categories` array in `public/index.html`
2. Update the prompt in `src/app.py` to handle new categories
3. Test with various combinations

### Adding New Tones

1. Update the `tones` array in `public/index.html`
2. Update the prompt in `src/app.py` to handle new tones
3. Test tone variations

### Customizing Styling

The frontend uses Tailwind CSS classes. Modify the classes in `public/index.html` to change the appearance.

## Security

- API tokens are handled securely using environment variables
- CORS is configured appropriately for the frontend
- No sensitive data is logged
- Input validation is performed on all API endpoints

## Performance

- Async HTTP calls for better performance
- Efficient React state management
- Optimized bundle size (single HTML file)
- Proper loading states and error handling

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the debug endpoint output
3. Check application logs
4. Verify Databricks configuration
