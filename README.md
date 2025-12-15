# Smart City Rome Dashboard

A basic Flask web application server for the Smart City Rome Dashboard project.

## Features

- Simple Flask web server with basic routes
- Health check endpoint
- API status endpoint
- Error handling for 404 and 500 errors
- Clean HTML homepage

## Requirements

- Conda (Anaconda or Miniconda)
- Python 3.9

## Setup

1. **Create or sync the conda environment:**

   ```bash
   ./create_or_sync_conda_env.sh
   ```

   This script will:
   - Create a new conda environment in `./.conda` if it doesn't exist
   - Install Python 3.9 and required dependencies
   - Install Flask from the requirements file

2. **Activate the conda environment:**

   ```bash
   conda activate ./.conda
   ```

## Running the Application

Once the environment is activated, run the Flask application:

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000` (accessible at `http://localhost:5000`).

## Available Endpoints

- **GET /** - Home page with welcome message and available endpoints
- **GET /health** - Health check endpoint returning JSON status
- **GET /api/status** - API status endpoint with service information

## Development

The application runs in debug mode by default when started with `python app.py`, which means:
- Auto-reload on code changes
- Detailed error messages
- Debug toolbar available

## Project Structure

```
.
├── app.py                          # Main Flask application
├── conda_env/
│   ├── environment.yml             # Conda environment specification
│   └── requirements.txt            # Python package requirements
├── create_or_sync_conda_env.sh    # Script to setup conda environment
├── dump_conda_env.sh              # Script to export environment
├── .gitignore                      # Git ignore patterns
└── README.md                       # This file
```

## License

This project is part of the Smart City Rome initiative.
