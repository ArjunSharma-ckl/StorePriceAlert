import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Set up the project root and Python path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import third-party packages
try:
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing third-party packages: {e}")
    print("Please install the required packages with: pip install -r requirements.txt")
    sys.exit(1)

# Import local modules
try:
    # First try direct imports (when running from project root)
    from code.api.client import DealScoutAPI
    from code.models import (
        Store, Product, Deal, PriceAlert, SearchResult,
        StoreChain, UserPreferences, ProductDetails
    )
    from code.config import settings
except ImportError:
    try:
        # Then try relative imports (when running from code directory)
        from api.client import DealScoutAPI
        from models import (
            Store, Product, Deal, PriceAlert, SearchResult,
            StoreChain, UserPreferences, ProductDetails
        )
        from config import settings
    except ImportError as e:
        print(f"Failed to import local modules: {e}")
        print(f"Current sys.path: {sys.path}")
        print(f"Current working directory: {os.getcwd()}")
        sys.exit(1)
        from config import settings
    except ImportError as e2:
        print(f"Alternative import also failed: {e2}")
        raise ImportError(f"Failed to import modules: {e}\n{e2}")

# ------------------------------
# Configuration
# ------------------------------
# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ------------------------------
# App Config / Theme
# ------------------------------
st.set_page_config(
    page_title="DealScout - Find the Best Deals Near You",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {border:1px solid #e5e7eb; padding:16px; border-radius:16px;}
    .pill {display:inline-block; padding:4px 10px; border-radius:999px; background:#eef2ff; margin-right:6px;}
    .muted {color:#6b7280;}
    .deal-card {border-left: 4px solid #4f46e5; padding-left: 12px; margin-bottom: 16px;}
    .price-tag {font-weight: 600; color: #1f2937;}
    .original-price {text-decoration: line-through; color: #9ca3af; margin-right: 8px;}
    .discount-badge {background: #e0e7ff; color: #4f46e5; font-size: 0.8em; padding: 2px 8px; border-radius: 999px;}
    .store-tag {background: #f3f4f6; padding: 4px 10px; border-radius: 6px; font-size: 0.9em;}
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------
# State Management
# ------------------------------
if 'api_client' not in st.session_state:
    try:
        st.session_state.api_client = DealScoutAPI()
        st.session_state.last_refresh = datetime.now()
        st.session_state.user_prefs = UserPreferences(
            default_zip_code=settings.DEFAULT_ZIP_CODE,
            default_radius_miles=settings.DEFAULT_RADIUS,
            preferred_stores=[StoreChain.WALMART.value, StoreChain.HEB.value]
        )
    except Exception as e:
        st.error(f"Failed to initialize API client: {str(e)}")
        st.stop()

# ------------------------------
# Helper Functions
# ------------------------------
def get_mock_deals() -> List[Dict]:
    """Generate mock deals data for development."""
    return [
        {
            'id': '1',
            'product_name': 'Organic Whole Milk - 1 Gallon',
            'brand': 'Organic Valley',
            'price': 4.99,
            'original_price': 5.99,
            'discount_percent': 17,
            'store_name': 'HEB',
            'store_id': 'HEB-123',
            'distance': 1.5,
            'image_url': 'https://m.media-amazon.com/images/I/71vUGB0GJEL._AC_UF1000,1000_QL80_.jpg',
            'category': 'Dairy'
        },
        {
            'id': '2',
            'product_name': 'Large Brown Eggs - 12 Count',
            'brand': 'Happy Egg Co',
            'price': 3.49,
            'original_price': 4.99,
            'discount_percent': 30,
            'store_name': 'Walmart',
            'store_id': 'WAL-456',
            'distance': 2.1,
            'image_url': 'https://m.media-amazon.com/images/I/81x5K5VvWEL._AC_UF1000,1000_QL80_.jpg',
            'category': 'Dairy'
        },
        {
            'id': '3',
            'product_name': 'Fresh Ground Beef - 1lb',
            'brand': 'Certified Angus Beef',
            'price': 5.99,
            'original_price': 7.99,
            'discount_percent': 25,
            'store_name': 'HEB',
            'store_id': 'HEB-123',
            'distance': 1.5,
            'image_url': 'https://m.media-amazon.com/images/I/71vUGB0GJEL._AC_UF1000,1000_QL80_.jpg',
            'category': 'Meat'
        },
        {
            'id': '4',
            'product_name': 'Organic Bananas - 1lb',
            'brand': 'Dole',
            'price': 0.59,
            'original_price': 0.79,
            'discount_percent': 25,
            'store_name': 'Whole Foods',
            'store_id': 'WF-789',
            'distance': 3.2,
            'image_url': 'https://m.media-amazon.com/images/I/61fZ+YAYGaL._AC_UF1000,1000_QL80_.jpg',
            'category': 'Produce'
        },
        {
            'id': '5',
            'product_name': 'Cage-Free Chicken Breast - 2.5lb',
            'brand': 'Perdue',
            'price': 8.99,
            'original_price': 12.99,
            'discount_percent': 31,
            'store_name': 'HEB',
            'store_id': 'HEB-123',
            'distance': 1.5,
            'image_url': 'https://m.media-amazon.com/images/I/61fZ+YAYGaL._AC_UF1000,1000_QL80_.jpg',
            'category': 'Meat'
        },
        {
            'id': '6',
            'product_name': 'Organic Strawberries - 16oz',
            'brand': 'Driscoll\'s',
            'price': 3.99,
            'original_price': 5.99,
            'discount_percent': 33,
            'store_name': 'Trader Joe\'s',
            'store_id': 'TJ-101',
            'distance': 4.5,
            'image_url': 'https://m.media-amazon.com/images/I/61fZ+YAYGaL._AC_UF1000,1000_QL80_.jpg',
            'category': 'Produce'
        }
    ]

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_deals(zip_code: str, radius: int, store_chains: List[str]) -> Tuple[List[Dict], int]:
    """Load deals from API with error handling and caching."""
    # Show loading state
    with st.spinner('Loading deals...'):
        try:
            # Try to get real data from API if available
            if 'api_client' in st.session_state and st.session_state.api_client is not None:
                try:
                    deals = st.session_state.api_client.get_todays_deals(
                        zip_code=zip_code,
                        radius=radius,
                        store_chains=store_chains
                    )
                    if not deals:
                        return get_mock_deals(), len(get_mock_deals())
                    return deals, len(deals)
                except Exception as api_error:
                    st.warning(f"API error: {str(api_error)}. Falling back to sample data.")
            
            # If we get here, either API client is not available or there was an error
            mock_deals = get_mock_deals()
            return mock_deals, len(mock_deals)
            
        except Exception as e:
            st.error(f"Error loading deals: {str(e)}")
            return [], 0

def render_deal_card(deal: Dict) -> None:
    """Render a single deal card in the UI."""
    # Ensure required fields have default values
    deal.setdefault('product_name', 'Unknown Product')
    deal.setdefault('price', 0.0)
    deal.setdefault('store_name', 'Unknown Store')
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{deal['product_name']}**")
        if deal.get('brand'):
            st.caption(deal['brand'])
            
        price_col, discount_col = st.columns([1, 2])
        with price_col:
            price = deal.get('price', 0)
            original_price = deal.get('original_price')
            
            if original_price and float(original_price) > float(price):
                st.markdown(
                    f"<div style='line-height: 1.2;'>"
                    f"<span style='display: block; text-decoration: line-through; color: #999; font-size: 0.9em;'>"
                    f"${float(original_price):.2f}"
                    f"</span>"
                    f"<span style='display: block; color: #e63946; font-weight: bold; font-size: 1.1em;'>"
                    f"${float(price):.2f}"
                    f"</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='line-height: 1.2;'>"
                    f"<span style='display: block; color: #e63946; font-weight: bold; font-size: 1.1em;'>"
                    f"${float(price):.2f}"
                    f"</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        
        with discount_col:
            if deal.get('discount_percent'):
                st.markdown(
                    f"<div style='background-color: #e63946; color: white; padding: 2px 8px; border-radius: 12px; display: inline-block; font-size: 0.8em;'>"
                    f"{deal['discount_percent']:.0f}% OFF"
                    f"</div>", 
                    unsafe_allow_html=True
                )
    
    with col2:
        st.markdown(
            f"<div style='background-color: #f0f2f6; padding: 4px 8px; border-radius: 12px; display: inline-block; font-size: 0.9em;'>"
            f"{deal['store_name']}"
            f"</div>", 
            unsafe_allow_html=True
        )
        if deal.get('distance'):
            st.caption(f"{deal['distance']:.1f} mi")
    
    st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)

def render_loading_placeholder() -> None:
    """Show a loading placeholder."""
    with st.spinner('Loading deals...'):
        st.info("If this takes too long, we're having trouble connecting to the API. Showing sample data...")
        time.sleep(2)  # Show the message for a moment
        return get_mock_deals()

# ------------------------------
# Sidebar
# ------------------------------
with st.sidebar:
    st.title("🔍 Filters")
    
    # Location
    st.subheader("Location")
    zip_code = st.text_input(
        "ZIP Code", 
        value=st.session_state.user_prefs.default_zip_code,
        max_chars=10,
        help="Enter a U.S. ZIP code"
    )
    
    radius_miles = st.slider(
        "Search Radius (miles)", 
        min_value=1, 
        max_value=50, 
        value=st.session_state.user_prefs.default_radius_miles,
        help="Distance around the ZIP to search for deals"
    )
    
    # Store Filters
    st.subheader("Stores")
    selected_chains = st.multiselect(
        "Select Stores",
        options=[chain.value for chain in StoreChain],
        default=st.session_state.user_prefs.preferred_stores,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    # Deal Filters
    st.subheader("Deal Types")
    deal_types = st.multiselect(
        "Show Deals",
        options=["Weekly Specials", "Clearance", "BOGO", "Digital Coupons", "Member Only"],
        default=["Weekly Specials", "Clearance"]
    )
    
    # Price Range
    price_range = st.slider(
        "Price Range",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 50.0),
        step=0.5,
        format="$%.2f"
    )
    
    # Refresh Button
    if st.button("🔃 Refresh Deals", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    st.markdown("---")
    st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%I:%M %p')}")

# ------------------------------
# Main Content
# ------------------------------
st.title("🛒 DealScout")
st.caption("Find the best deals at stores near you")

# Load data with loading state
with st.spinner('Loading deals...'):
    deals, deals_count = load_deals(zip_code, radius_miles, selected_chains)

# KPI Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Active Deals", deals_count)
with col2:
    st.metric("Stores Found", len({deal.get('store_id', '') for deal in deals}) if deals else 0)
with col3:
    avg_savings = sum(deal.get('discount_percent', 0) for deal in deals) / len(deals) if deals else 0
    st.metric("Average Savings", f"{avg_savings:.1f}%")

st.markdown("---")

# Tabs
tab_names = ["🏷️ Today's Deals", "📊 Price Trends"]
tabs = st.tabs(tab_names)

tab_deals = tabs[0]
tab_trends = tabs[1]

with tab_deals:
    st.subheader("Today's Deals by Store/ZIP")
    
    # Filters
    c1, c2, c3 = st.columns([2,2,1])
    with c1:
        search_query = st.text_input("Quick Search (title, brand, category)", 
                                   placeholder="e.g., whole milk 1 gallon", 
                                   key="quick_search").lower()
    with c2:
        category_filter = st.selectbox(
            "Category", 
            ["All"] + sorted(list(set(deal.get('category', 'Other') for deal in deals))),
            index=0, 
            key="category_filter"
        )
    with c3:
        sort_option = st.selectbox(
            "Sort by", 
            ["Best Value", "Price (Low to High)", "Discount %", "Distance"], 
            index=0, 
            key="sort_option"
        )
    
    st.markdown(
        f'<span style="display: inline-block; background: #f0f2f6; padding: 4px 12px; '
        f'border-radius: 16px; margin-right: 8px; font-size: 0.9em;">'
        f'ZIP: {zip_code}</span>'
        f'<span style="display: inline-block; background: #f0f2f6; padding: 4px 12px; '
        f'border-radius: 16px; font-size: 0.9em;">'
        f'Radius: {radius_miles} mi</span>', 
        unsafe_allow_html=True
    )
    
    # Filter deals based on search and category
    filtered_deals = []
    if deals:
        for deal in deals:
            # Apply search filter
            if search_query:
                search_fields = [
                    deal.get('product_name', '').lower(),
                    deal.get('brand', '').lower(),
                    deal.get('category', '').lower()
                ]
                if not any(search_query in field for field in search_fields if field):
                    continue
            
            # Apply category filter
            if category_filter != "All" and deal.get('category') != category_filter:
                continue
                
            filtered_deals.append(deal)
    
    # Show results
    if not filtered_deals:
        st.info("No deals match your filters. Try adjusting your search criteria.")
        
        # Show sample data button
        if st.button("Show sample data"):
            sample_deals = get_mock_deals()
            for deal in sample_deals:
                render_deal_card(deal)
    else:
        # Apply sorting
        if sort_option == "Price (Low to High)":
            filtered_deals.sort(key=lambda x: x.get('price', float('inf')))
        elif sort_option == "Discount %":
            filtered_deals.sort(key=lambda x: x.get('discount_percent', 0), reverse=True)
        elif sort_option == "Distance":
            filtered_deals.sort(key=lambda x: x.get('distance', float('inf')))
        else:  # Best Value (default)
            filtered_deals.sort(
                key=lambda x: (x.get('discount_percent', 0), -x.get('price', 0)), 
                reverse=True
            )
        
        # Display deals
        for deal in filtered_deals:
            render_deal_card(deal)
        
        st.info(f"Showing {len(filtered_deals)} of {len(deals)} total deals")

with tab_trends:
    st.subheader("Price Trends")
    
    # Sample price history data for different categories
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Generate realistic price trends for different categories
    dairy_trend = [4.99, 4.79, 4.89, 4.95, 4.99, 5.29, 5.49, 5.29, 5.19, 4.99, 4.89, 4.79]
    meat_trend = [8.99, 9.29, 8.79, 8.99, 9.49, 9.99, 10.49, 10.29, 9.99, 9.49, 9.29, 9.49]
    produce_trend = [3.49, 3.29, 3.19, 2.99, 2.79, 2.99, 3.29, 3.49, 3.29, 2.99, 3.19, 3.49]
    
    # Create the trend chart
    fig = px.line(
        title="<b>Average Price Trends by Category (2025)</b>",
        labels={"value": "Price ($)", "index": "Month", "variable": "Category"},
        template="plotly_white"
    )
    
    # Add traces for each category
    fig.add_scatter(x=months, y=dairy_trend, name="Dairy", line=dict(color='#4C78A8'))
    fig.add_scatter(x=months, y=meat_trend, name="Meat", line=dict(color='#E45756'))
    fig.add_scatter(x=months, y=produce_trend, name="Produce", line=dict(color='#54A24B'))
    
    # Update layout
    fig.update_layout(
        hovermode="x unified",
        xaxis_title=None,
        yaxis_title="Average Price ($)",
        legend_title="Category",
        height=500,
        title_x=0.5,
        title_font=dict(size=18),
        margin=dict(t=60, b=20, l=60, r=40)
    )
    
    # Add annotations for current month
    current_month = datetime.now().month - 1  # 0-based
    current_dairy = dairy_trend[current_month]
    
    fig.add_annotation(
        x=months[current_month],
        y=current_dairy,
        text=f"Current: ${current_dairy:.2f}",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Add some summary metrics
    st.markdown("### Monthly Price Changes")
    
    # Calculate month-over-month changes
    def calculate_mom_change(prices):
        if len(prices) < 2:
            return 0
        return ((prices[-1] - prices[-2]) / prices[-2]) * 100
    
    dairy_change = calculate_mom_change(dairy_trend)
    meat_change = calculate_mom_change(meat_trend)
    produce_change = calculate_mom_change(produce_trend)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dairy", f"${dairy_trend[-1]:.2f}", f"{dairy_change:+.1f}% from last month")
    with col2:
        st.metric("Meat", f"${meat_trend[-1]:.2f}", f"{meat_change:+.1f}% from last month")
    with col3:
        st.metric("Produce", f"${produce_trend[-1]:.2f}", f"{produce_change:+.1f}% from last month")

# ------------------------------
# Footer
# ------------------------------
st.markdown("---")
st.caption("© 2025 DealScout - Find the best deals in your area")

# Error handling for API issues
if 'api_error' in st.session_state:
    st.error(st.session_state.api_error)
    del st.session_state.api_error
