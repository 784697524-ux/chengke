import os
import sys

from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_mpserverless20190615.client import Client
from alibabacloud_mpserverless20190615 import models as mp_models


def client() -> Client:
    config = open_api_models.Config(
        access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
        region_id="cn-hangzhou",
        endpoint="mpserverless.aliyuncs.com",
    )
    return Client(config)


def main():
    raw_ids = os.environ.get("EMAS_DELETE_SPACE_IDS", "")
    space_ids = [item.strip() for item in raw_ids.split(",") if item.strip()]
    if not space_ids:
        raise RuntimeError("EMAS_DELETE_SPACE_IDS is empty")

    cli = client()
    for space_id in space_ids:
        try:
            cli.delete_space(mp_models.DeleteSpaceRequest(space_id=space_id))
            print(f"DELETED_SPACE={space_id}")
        except Exception as exc:
            message = str(exc)
            if "NotFound" in message or "not found" in message.lower():
                print(f"SPACE_ALREADY_ABSENT={space_id}")
                continue
            raise


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise
