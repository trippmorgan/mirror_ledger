# src/mirror_ledger/__main__.py

import uvicorn

def main():
    """Main function to run the Uvicorn server."""
    print("--- Starting Mirror Ledger Service ---")
    print("Components will be initialized by the application's lifespan manager.")
    print("API documentation available at http://127.0.0.1:8000/docs")

    uvicorn.run(
        # Point to the app object in our newly configured server file
        "mirror_ledger.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src/mirror_ledger"]
    )

if __name__ == "__main__":
    main()