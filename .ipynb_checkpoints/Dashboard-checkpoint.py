import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

# ===================== HELPER FUNCTION =====================

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_date').agg({
        "order_id": "nunique",
        "total_price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "total_price": "revenue"
    }, inplace=True)
    return daily_orders_df


def create_sum_order_items_df(df):
    return df.groupby("product_name").quantity_x.sum().sort_values(ascending=False).reset_index()


def create_bygender_df(df):
    bygender_df = df.groupby("gender").customer_id.nunique().reset_index()
    bygender_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bygender_df


def create_byage_df(df):
    byage_df = df.groupby("age_group").customer_id.nunique().reset_index()
    byage_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    byage_df['age_group'] = pd.Categorical(
        byage_df['age_group'], ["Youth", "Adults", "Seniors"]
    )
    byage_df = byage_df.sort_values("age_group")
    return byage_df


def create_bystate_df(df):
    bystate_df = df.groupby("state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df


def create_rfm_df(df):
    rfm_df = df.groupby("customer_id", as_index=False).agg({
        "order_date": "max",
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_date"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(
        lambda x: (recent_date - x).days
    )
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df


# ===================== LOAD DATA =====================

all_df = pd.read_csv("all_data.csv")

datetime_columns = ["order_date", "delivery_date"]
all_df.sort_values(by="order_date", inplace=True)
all_df.reset_index(drop=True, inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# ===================== SIDEBAR =====================

min_date = all_df["order_date"].min()
max_date = all_df["order_date"].max()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")

    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# ===================== FILTER DATA =====================

main_df = all_df[
    (all_df["order_date"] >= pd.Timestamp(start_date)) &
    (all_df["order_date"] <= pd.Timestamp(end_date))
]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bygender_df = create_bygender_df(main_df)
byage_df = create_byage_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# ===================== DASHBOARD =====================

st.header('Dicoding Collection Dashboard ✨')

# ----- DAILY ORDERS -----
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO')
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_date"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

# ----- BEST & WORST PRODUCT -----
st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

best_df = sum_order_items_df.head(5).copy()
worst_df = sum_order_items_df.sort_values(by="quantity_x", ascending=True).head(5).copy()

sns.barplot(
    x="quantity_x",
    y="product_name",
    data=best_df,
    hue="product_name",
    palette=["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"],
    legend=False,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(
    x="quantity_x",
    y="product_name",
    data=worst_df,
    hue="product_name",
    palette=["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"],
    legend=False,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

# ----- CUSTOMER DEMOGRAPHICS -----
st.subheader("Customer Demographics")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(20, 10))
    gender_sorted = bygender_df.sort_values(by="customer_count", ascending=False)
    sns.barplot(
        y="customer_count",
        x="gender",
        data=gender_sorted,
        hue="gender",
        palette=["#90CAF9", "#D3D3D3"],
        legend=False,
        ax=ax
    )
    ax.set_title("Number of Customer by Gender", loc="center", fontsize=50)
    ax.set_ylabel("Number of Customers", fontsize=30)
    ax.set_xlabel("Gender", fontsize=30)
    ax.tick_params(axis='x', labelsize=35)
    ax.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(
        y="customer_count",
        x="age_group",
        data=byage_df,
        hue="age_group",
        palette=["#D3D3D3", "#90CAF9", "#D3D3D3"],
        legend=False,
        ax=ax
    )
    ax.set_title("Number of Customer by Age Group", loc="center", fontsize=50)
    ax.set_ylabel("Number of Customers", fontsize=30)
    ax.set_xlabel("Age Group", fontsize=30)
    ax.tick_params(axis='x', labelsize=35)
    ax.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)

fig, ax = plt.subplots(figsize=(20, 10))
state_sorted = bystate_df.sort_values(by="customer_count", ascending=False)
state_colors = ["#90CAF9" if i == 0 else "#D3D3D3" for i in range(len(state_sorted))]
sns.barplot(
    x="customer_count",
    y="state",
    data=state_sorted,
    hue="state",
    palette=state_colors,
    legend=False,
    ax=ax
)
ax.set_title("Number of Customer by State", loc="center", fontsize=30)
ax.set_ylabel("State", fontsize=20)
ax.set_xlabel("Number of Customers", fontsize=20)
ax.tick_params(axis='y', labelsize=15)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

# ----- RFM ANALYSIS -----
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO')
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
rfm_colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

recency_df = rfm_df.sort_values(by="recency", ascending=True).head(5).copy()
sns.barplot(
    y="recency",
    x="customer_id",
    data=recency_df,
    hue="customer_id",
    palette=rfm_colors,
    legend=False,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)

frequency_df = rfm_df.sort_values(by="frequency", ascending=False).head(5).copy()
sns.barplot(
    y="frequency",
    x="customer_id",
    data=frequency_df,
    hue="customer_id",
    palette=rfm_colors,
    legend=False,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)

monetary_df = rfm_df.sort_values(by="monetary", ascending=False).head(5).copy()
sns.barplot(
    y="monetary",
    x="customer_id",
    data=monetary_df,
    hue="customer_id",
    palette=rfm_colors,
    legend=False,
    ax=ax[2]
)
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)

st.pyplot(fig)

st.caption("Copyright © Dicoding")