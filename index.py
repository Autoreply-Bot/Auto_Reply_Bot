from app import app

# Vercel expects 'app' variable
# This wrapper makes Flask work on Vercel serverless

# For Vercel, expose as 'app'
# Vercel will call it

# Health check
if __name__ == "__main__":
    app.run()
