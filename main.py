import os
import time
import requests
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import models, dnspod_client


# update dns.
class DynamicDNSUpdater:
    def __init__(self, domain, sub_domain, record_id, app_id, app_secret):
        self.domain = domain
        self.sub_domain = sub_domain
        self.record_id = record_id
        self.app_id = app_id
        self.app_secret = app_secret
        self.current_ip = None
        self.cred = credential.Credential(self.app_id, self.app_secret)
        self.client = dnspod_client.DnspodClient(self.cred, "ap-shanghai")

    def get_current_ip(self):
        response = requests.get("https://api.ipify.org?format=json")
        data = response.json()
        self.current_ip = data['ip']

    def list_record_value(self):
        try:
            req = models.DescribeRecordRequest()
            req.Domain = self.domain
            req.RecordId = self.record_id
            resp = self.client.DescribeRecord(req)
            print(resp.to_json_string())
            return resp.RecordInfo.Value
        except Exception as e:
            print("occurs error: " + e.with_traceback)
            return None

    def update_dns_record(self):
        try:
            req = models.ModifyRecordRequest()
            req.Domain = self.domain
            req.SubDomain = self.sub_domain
            req.Value = self.current_ip
            req.RecordId = self.record_id
            req.RecordLine = '默认'
            resp = self.client.ModifyDynamicDNS(req)
            print(resp.to_json_string())
            return resp.RecordId == self.record_id
        except TencentCloudSDKException as err:
            print(err)
            return False

    def run(self):
        self.get_current_ip()
        print("New IP:", self.current_ip)
        if self.current_ip == self.list_record_value():
            print("skip to update for same ip")
            return True
        if self.update_dns_record():
            print("DNS record updated successfully.")
        else:
            print("DNS record update failed.")


# main
if __name__ == '__main__':
    domain = os.getenv("DOMAIN", None)
    sub_domain = os.getenv("SUB_DOMAIN", None)
    record_id = int(os.getenv("RECORD_ID", ''))
    app_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    app_secret = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    default_interval = int(os.environ.get("DEFAULT_INTERVAL", 60))

    if domain and sub_domain and record_id and app_id and app_secret:
        updater = DynamicDNSUpdater(domain, sub_domain, record_id, app_id, app_secret)
        while True:
            time.sleep(default_interval)
            try:
                updater.run()
            except Exception as e:
                print("occurs error: " + e.with_traceback)
    else:
        print("Missing required environment variables.")
