import os
import shutil
import json

def build_deployment():
    src_dir = r"c:\Users\siddh\OneDrive\Desktop\sih 2026"
    deploy_dir = os.path.join(src_dir, "aerova-deploy")
    
    # 1. Create clean deploy directory
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    os.makedirs(os.path.join(deploy_dir, "api"))
    os.makedirs(os.path.join(deploy_dir, "data"))
    os.makedirs(os.path.join(deploy_dir, "data", "dgca-data"))
    
    print("Creating deployment folder at:", deploy_dir)
    
    # 2. Copy Frontend
    shutil.copy2(os.path.join(src_dir, "index.html"), os.path.join(deploy_dir, "index.html"))
    if os.path.exists(os.path.join(src_dir, "favicon.png")):
        shutil.copy2(os.path.join(src_dir, "favicon.png"), os.path.join(deploy_dir, "favicon.png"))
    
    # 3. Copy API Backend and update paths
    api_src = os.path.join(src_dir, "api", "index.py")
    with open(api_src, "r", encoding="utf-8") as f:
        api_content = f.read()
    
    # Update paths in api_content for the flattened deployment structure
    api_content = api_content.replace(
        "DB_PATH = os.path.join(BASE_DIR, 'scrapers', 'engine', 'flights.db')",
        "DB_PATH = os.path.join(BASE_DIR, 'data', 'flights.db')"
    )
    api_content = api_content.replace(
        "STATIC_DATA_DIR = os.path.join(BASE_DIR, 'scrapers', 'pipeline', 'static_data')",
        "STATIC_DATA_DIR = os.path.join(BASE_DIR, 'data')"
    )
    api_content = api_content.replace(
        "traffic_dir = os.path.join(root_dir, \"india-aviation-traffic\", \"2025_data\")",
        "traffic_dir = os.path.join(root_dir, \"data\", \"dgca-data\")"
    )
    api_content = api_content.replace(
        "os.path.join(root_dir, \"TARIFF-SHEET-AS-ON-28-NOV-24.pdf\")",
        "os.path.join(root_dir, \"data\", \"TARIFF-SHEET-AS-ON-28-NOV-24.pdf\")"
    )
    
    # Write updated api/index.py
    with open(os.path.join(deploy_dir, "api", "index.py"), "w", encoding="utf-8") as f:
        f.write(api_content)
        
    # 4. Copy Data
    print("Copying Data...")
    db_src = os.path.join(src_dir, "scrapers", "engine", "flights.db")
    if os.path.exists(db_src):
        shutil.copy2(db_src, os.path.join(deploy_dir, "data", "flights.db"))
    
    weights_src = os.path.join(src_dir, "scrapers", "pipeline", "static_data", "route_weights.csv")
    if os.path.exists(weights_src):
        shutil.copy2(weights_src, os.path.join(deploy_dir, "data", "route_weights.csv"))
        
    tariffs_src = os.path.join(src_dir, "scrapers", "pipeline", "static_data", "tariff_base_prices.csv")
    if os.path.exists(tariffs_src):
        shutil.copy2(tariffs_src, os.path.join(deploy_dir, "data", "tariff_base_prices.csv"))
        
    pdf_src = os.path.join(src_dir, "TARIFF-SHEET-AS-ON-28-NOV-24.pdf")
    if os.path.exists(pdf_src):
        shutil.copy2(pdf_src, os.path.join(deploy_dir, "data", "TARIFF-SHEET-AS-ON-28-NOV-24.pdf"))
        
    dgca_src_dir = os.path.join(src_dir, "india-aviation-traffic", "2025_data")
    if os.path.exists(dgca_src_dir):
        for f in os.listdir(dgca_src_dir):
            if f.endswith(".csv"):
                shutil.copy2(os.path.join(dgca_src_dir, f), os.path.join(deploy_dir, "data", "dgca-data", f))
                
    # 5. Create Vercel Configuration
    vercel_config = {
        "version": 2,
        "builds": [
            { "src": "api/index.py", "use": "@vercel/python" },
            { "src": "index.html", "use": "@vercel/static" }
        ],
        "routes": [
            { "src": "/api/(.*)", "dest": "/api/index.py" },
            { "src": "/dgca-data/(.*)", "dest": "/api/index.py" },
            { "src": "/pdfs/(.*)", "dest": "/api/index.py" },
            { "src": "/(.*)", "dest": "/index.html" }
        ]
    }
    with open(os.path.join(deploy_dir, "vercel.json"), "w") as f:
        json.dump(vercel_config, f, indent=2)
        
    # 6. Create requirements.txt
    reqs = "fastapi==0.104.1\nuvicorn==0.23.2\npandas==2.1.2\n"
    with open(os.path.join(deploy_dir, "requirements.txt"), "w") as f:
        f.write(reqs)
        
    print("Deployment folder generated successfully!")

if __name__ == "__main__":
    build_deployment()
