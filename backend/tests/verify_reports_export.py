import sys
import os
import asyncio
from unittest.mock import MagicMock
from datetime import datetime, date

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.api.reports import (
    get_inventory_valuation_report, 
    get_consumption_report,
    get_waste_analysis_report,
    get_theoretical_vs_actual_report,
    get_purchases_report,
    get_rotation_analysis_report,
    get_obsolete_products_report
)
from backend.models.database import User, Product, Category, StockMovement, Invoice, WasteLog, Provider

async def test_exports():
    print("🧪 Verificando exportación de reportes...")
    
    # Mock resources
    mock_user = User(id=1, restaurant_id=1, role="admin", email="admin@test.com")
    mock_db = MagicMock()
    
    # Mock data queries
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    
    endpoints = [
        (get_inventory_valuation_report, {}),
        (get_consumption_report, {"date_from": "2023-01-01", "date_to": "2023-01-31", "group_by": "category"}),
        (get_waste_analysis_report, {"date_from": "2023-01-01", "date_to": "2023-01-31"}),
        (get_theoretical_vs_actual_report, {"date_from": "2023-01-01", "date_to": "2023-01-31"}),
        (get_purchases_report, {"date_from": "2023-01-01", "date_to": "2023-01-31"}),
        (get_rotation_analysis_report, {"days": 30}),
        (get_obsolete_products_report, {"days_without_movement": 30})
    ]
    
    for endpoint, params in endpoints:
        func_name = endpoint.__name__
        print(f"\nTesting {func_name}...")
        
        try:
            # Test Excel
            params["format"] = "excel"
            res_excel = await endpoint(**params, current_user=mock_user, db=mock_db)
            if res_excel.__class__.__name__ == "StreamingResponse":
                print(f"✅ Excel OK")
            else:
                print(f"❌ Excel Failed: Returned {type(res_excel)}")
                
            # Test PDF
            params["format"] = "pdf"
            res_pdf = await endpoint(**params, current_user=mock_user, db=mock_db)
            if res_pdf.__class__.__name__ == "StreamingResponse":
                print(f"✅ PDF OK")
            else:
                print(f"❌ PDF Failed: Returned {type(res_pdf)}")
                
        except Exception as e:
            print(f"❌ Error crítico en {func_name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_exports())
