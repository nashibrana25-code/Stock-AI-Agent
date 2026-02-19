#!/usr/bin/env python3
"""Deploy script for ASX AI Platform frontend.

Builds the frontend and deploys the dist folder to Vercel.
This avoids the parent vercel.json inheritance issue.

Usage: python deploy_frontend.py
"""
import subprocess
import shutil
import json
import os

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend')
DIST_DIR = os.path.join(FRONTEND_DIR, 'dist')

VERCEL_PROJECT = {
    "projectId": "prj_GwCAZFXZx78zcSKhIjTgZqJtqqZz",
    "orgId": "team_xmv7qnf4rN0B1SExvGsshpvc"
}

DIST_VERCEL_JSON = {
    "version": 2,
    "buildCommand": "",
    "outputDirectory": ".",
    "framework": None,
    "rewrites": [
        {"source": "/(.*)", "destination": "/index.html"}
    ]
}


def main():
    print("🔨 Building frontend...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Build failed:\n{result.stderr}")
        return 1
    print("✅ Build complete")

    # Add vercel.json and .vercel/project.json to dist
    with open(os.path.join(DIST_DIR, "vercel.json"), "w") as f:
        json.dump(DIST_VERCEL_JSON, f, indent=2)

    vercel_dir = os.path.join(DIST_DIR, ".vercel")
    os.makedirs(vercel_dir, exist_ok=True)
    with open(os.path.join(vercel_dir, "project.json"), "w") as f:
        json.dump(VERCEL_PROJECT, f)

    print("🚀 Deploying to Vercel...")
    result = subprocess.run(
        ["vercel", "--prod", "--yes"],
        cwd=DIST_DIR,
        shell=True,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Deploy failed:\n{result.stderr}")
        return 1

    print("✅ Frontend deployed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
