import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting TeamPulse Enterprise Web Server Preview")
    print("Access Link: http://127.0.0.1:8000")
    print("Demo Manager Credentials: Username: Admin | Password: admin123")
    print("Demo Employee Credentials: Username: Alex | Password: emp123")
    print("=" * 60)
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)
