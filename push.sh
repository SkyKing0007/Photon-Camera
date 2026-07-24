#!/bin/bash
# Run this to push to your GitHub repo
# You'll need a GitHub Personal Access Token
# Get one at: https://github.com/settings/tokens

read -p "Enter your GitHub token: " TOKEN

git remote add origin https://${TOKEN}@github.com/SkyKing0007/Photon-Camera.git 2>/dev/null
git branch -M main
git push -u origin main --force

echo "Done! Check https://github.com/SkyKing0007/Photon-Camera"
