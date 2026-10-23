from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator

from src.config import INTERVAL_MINUTES, CHANGE_THRESHOLD, LOOKBACK_STEPS
from src.fetch_price import fetch_price
from src.storage_manager import LocalStorageManager
from src.price_monitor import (
    check_alert_condition,
    send_email_alert,
    sender_email,
    gmail_app_pwd,
    receiver_email,
)

default_args = {
    "owner": "Aayam Raj Shakya",
    "retries": 0,
}

with DAG(
    dag_id="btc_price_monitor",
    description=f"Fetch bitcoin price every {INTERVAL_MINUTES} minutes and alert if the price changes by {CHANGE_THRESHOLD}%",
    default_args=default_args,
    schedule=f"*/{INTERVAL_MINUTES} * * * *",
    start_date=datetime(2026, 10, 1),
    catchup=False,
) as dag:

    def eval_price_change(**kwargs):
        ti = kwargs["ti"]

        # fetch current price
        curr_data = fetch_price()
        curr_price = curr_data["price_usd"]
        print(f"Current btc price: ${curr_price:,.2f}")

        # save data to local storage
        handler = LocalStorageManager()
        handler.upload_data(curr_data)

        # fetch past prices
        price_history = handler.get_price_history(steps=LOOKBACK_STEPS)

        if len(price_history) < LOOKBACK_STEPS:
            print(
                f"Insufficient data. We need {LOOKBACK_STEPS} data points to calculate 1-hr change"
            )
            return "no_email_alert"

        past_record = price_history[LOOKBACK_STEPS - 1]
        prev_price = past_record["price_usd"]
        print(f"Price 1-hr ago ({past_record['timestamp_utc']}): ${prev_price:,.2f}")

        # check against threshold
        alert_bool, pct_change = check_alert_condition(
            curr_price=curr_price,
            prev_price=prev_price,
            threshold_pct=CHANGE_THRESHOLD,
        )

        if alert_bool:
            ti.xcom_push(key="curr_price", value=curr_price)
            ti.xcom_push(key="prev_price", value=prev_price)
            ti.xcom_push(key="pct_change", value=pct_change)
            return "email_alert"

        return "no_email_alert"

    def handle_email_alert(**kwargs):
        ti = kwargs["ti"]
        curr_price = ti.xcom_pull(
            task_ids="eval_price_change_and_branch_out", key="curr_price"
        )
        prev_price = ti.xcom_pull(
            task_ids="eval_price_change_and_branch_out", key="prev_price"
        )
        pct_change = ti.xcom_pull(
            task_ids="eval_price_change_and_branch_out", key="pct_change"
        )

        send_email_alert(
            sender=sender_email,
            sender_password=gmail_app_pwd,
            receiver=receiver_email,
            curr_price=curr_price,
            prev_price=prev_price,
            pct_change=pct_change,
        )

    check_price_branch = BranchPythonOperator(
        task_id="eval_price_change_and_branch_out",
        python_callable=eval_price_change,
    )

    no_alert = EmptyOperator(
        task_id="no_email_alert",
    )

    yes_alert = PythonOperator(
        task_id="email_alert",
        python_callable=handle_email_alert,
    )

    # task dependencies
    check_price_branch >> [no_alert, yes_alert]

    # we could also do
    # check_price_branch.set_downstream([no_alert, yes_alert])
    ## https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#task-dependencies
