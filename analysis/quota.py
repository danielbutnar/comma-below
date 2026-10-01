"""Print the Kaggle Model Proxy quota (the CLI 2.2.4 has no `kaggle b quota`).

Run with the Kaggle CLI's own Python so the SDK and login are available:
  ~/.local/share/uv/tools/kaggle/Scripts/python.exe analysis/quota.py
"""

from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.models.types.model_proxy_api_service import ApiGetModelProxyQuotasRequest

api = KaggleApi()
api.authenticate()
with api.build_kaggle_client() as kaggle:
    resp = kaggle.models.model_proxy_api_client.get_model_proxy_quotas(ApiGetModelProxyQuotasRequest())
for b in resp.quota_balances or []:
    used, total = b.quota_used, b.total_quota_allowed
    print(f"{str(b.refill_period):40s} used ${used:.2f}  remaining ${max(0.0, total - used):.2f}  "
          f"total ${total:.2f}  refills {b.refill_time}")
