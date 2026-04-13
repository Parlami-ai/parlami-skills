#!/usr/bin/env python3
"""
Upload image asset to Google Ads asset group.
Usage: python upload-image-asset.py <asset_group_id> <image_path> <headline1> <headline2> <description>
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path.home() / "Projects" / "parlami_ai"
sys.path.insert(0, str(project_root))

from utils.secrets import Config
from google.ads.googleads.client import GoogleAdsClient

def upload_image_asset(asset_group_id, image_path, headline1, headline2, description):
    """Upload image to Google Ads and link to asset group"""
    
    credentials = {
        'developer_token': Config.GOOGLE_ADS_DEVELOPER_TOKEN,
        'client_id': Config.GOOGLE_ADS_CLIENT_ID,
        'client_secret': Config.GOOGLE_ADS_CLIENT_SECRET,
        'refresh_token': Config.GOOGLE_ADS_REFRESH_TOKEN,
        'use_proto_plus': True
    }
    
    client = GoogleAdsClient.load_from_dict(credentials)
    customer_id = Config.GOOGLE_ADS_CUSTOMER_ID
    
    # Step 1: Create image asset
    asset_service = client.get_service("AssetService")
    asset_op = client.get_type("AssetOperation")
    asset = asset_op.create
    
    # Read image file
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    asset.image_asset.data = image_data
    asset.name = Path(image_path).stem  # Use filename as asset name
    asset.type_ = client.enums.AssetTypeEnum.IMAGE
    
    try:
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_op]
        )
        asset_rn = asset_response.results[0].resource_name
        print(f"✅ Created image asset: {asset_rn}")
        
        # Step 2: Link image to asset group
        ag_asset_service = client.get_service("AssetGroupAssetService")
        link_op = client.get_type("AssetGroupAssetOperation")
        link = link_op.create
        link.asset_group = f"customers/{customer_id}/assetGroups/{asset_group_id}"
        link.asset = asset_rn
        link.field_type = client.enums.AssetFieldTypeEnum.MARKETING_IMAGE
        
        link_response = ag_asset_service.mutate_asset_group_assets(
            customer_id=customer_id,
            operations=[link_op]
        )
        print(f"✅ Linked image to asset group {asset_group_id}")
        
        return asset_rn
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python upload-image-asset.py <asset_group_id> <image_path> <headline1> <headline2> <description>")
        sys.exit(1)
    
    ag_id = sys.argv[1]
    img_path = sys.argv[2]
    h1 = sys.argv[3]
    h2 = sys.argv[4]
    desc = sys.argv[5]
    
    upload_image_asset(ag_id, img_path, h1, h2, desc)
