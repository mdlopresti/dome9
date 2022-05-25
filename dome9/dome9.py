# -*- coding: utf-8 -*-
import os
import json
import requests
from requests import ConnectionError


class Dome9(object):

    def __init__(self, key=None, secret=None, endpoint='https://api.dome9.com', apiVersion='v2'):
        self.key = None
        self.secret = None
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        self.endpoint = endpoint + '/{}/'.format(apiVersion)
        self._load_credentials(key, secret)

    # ------ System Methods ------
    # ----------------------------

    def _load_credentials(self, key, secret):
        if key and secret:
            self.key = key
            self.secret = secret
        elif os.getenv('DOME9_ACCESS_KEY') and os.getenv('DOME9_SECRET_KEY'):
            self.key = os.getenv('DOME9_ACCESS_KEY')
            self.secret = os.getenv('DOME9_SECRET_KEY')
        else:
            raise ValueError('No provided credentials')

    def _request(self, method, route, payload=None):
        res = url = err = jsonObject = None
        _payload = json.dumps(payload)
        try:
            url = '{}{}'.format(self.endpoint, route)
            if method == 'get':
                res = requests.get(url=url, params=_payload, headers=self.headers, auth=(self.key, self.secret))
            elif method == 'post':
                res = requests.post(url=url, data=_payload, headers=self.headers, auth=(self.key, self.secret))
            elif method == 'patch':
                res = requests.patch(url=url, json=_payload, headers=self.headers, auth=(self.key, self.secret))
            elif method == 'put':
                res = requests.put(url=url, data=_payload, headers=self.headers, auth=(self.key, self.secret))
            elif method == 'delete':
                res = requests.delete(url=url, params=_payload, headers=self.headers, auth=(self.key, self.secret))
                return bool(res.status_code == 204)

        except requests.ConnectionError as ex:
            raise ConnectionError(url, ex.message)

        # If status_code is in range 200-209
        if str(res.status_code)[0] == '2':
            try:
                if res.content:
                    jsonObject = res.json()
            except Exception as ex:
                err = {'code': res.status_code, 'message': ex.message, 'content': res.content}
        else:
            err = {'code': res.status_code, 'message': res.reason, 'content': res.content}

        if err:
            raise Exception(err)
        return jsonObject

    def _get(self, route, payload=None):
        return self._request('get', route, payload)

    def _post(self, route, payload=None):
        return self._request('post', route, payload)

    def _patch(self, route, payload=None):
        return self._request('patch', route, payload)

    def _put(self, route, payload=None):
        return self._request('put', route, payload)

    def _delete(self, route, payload=None):
        return self._request('delete', route, payload)

    # ------------------   Accounts   ------------------
    # --------------------------------------------------

    def get_cloud_account(self, id):
        """Get a Cloud Account

        Args:
            id (str): ID of the Cloud Account

        Returns:
            dict: Cloud Account object.

        Response object:
            .. literalinclude:: schemas/AwsCloudAccount.json
        """
        return self._get(route='CloudAccounts/%s' % str(id))

    def list_aws_accounts(self):
        """List AWS accounts

        Returns:
            list: List of AWS Cloud Accounts.

        Response object:
            .. literalinclude:: schemas/AwsCloudAccount.json
        """
        return self._get(route='CloudAccounts')

    def list_azure_accounts(self):
        """List Azure accounts

        Returns:
            list: List of Azure Cloud Accounts.

        Response object:
            .. literalinclude:: schemas/AzureCloudAccount.json
        """
        return self._get(route='AzureCloudAccount')

    def list_google_accounts(self):
        """List Google Cloud Accounts

        Returns:
            list: List of Google accounts.

        Response object:
            .. literalinclude:: schemas/GoogleCloudAccount.json
        """
        return self._get(route='GoogleCloudAccount')

    def list_kubernetes_accounts(self):
        """List Kubernetes accounts

        Returns:
            list: List of Kubernetes accounts.

        Response object:
            .. literalinclude:: schemas/KubernetesCloudAccount.json
        """
        return self._get(route='KubernetesAccount')

    def list_cloud_accounts(self):
        """List all accounts (AWS, Azure, GCP & Kubernetes)

        Returns:
            list: List of Cloud Accounts.

        Response object:
            .. literalinclude:: schemas/AwsCloudAccount.json
        """
        accounts = self.list_azure_accounts()
        accounts.extend(self.list_aws_accounts())
        accounts.extend(self.list_google_accounts())
        accounts.extend(self.list_kubernetes_accounts())
        return accounts

    def create_aws_account(self, name, secret, roleArn):
        account = {
            "vendor": "aws",
            "name": "test",
            "credentials": {"type": "RoleBased", "secret": "", "arn": ""},
            "fullProtection": False,
            "allowReadOnly": True,
            "lambdaScanner": False
            }
        account['name'] = name
        account['credentials']['secret'] = secret
        account['credentials']['arn'] = roleArn
        return self._post(route='CloudAccounts', payload=account)

    # ------------------- Assets -------------------
    # ----------------------------------------------

    def list_protected_assets(self, textSearch="", filters=[], pagesize=1000):
        """List all Cloud Assets

        Args:
            textSearch (list): Filter query by using text string. (i.e.: prod-uk)
            filters (list): List of filters. `[{name: "platform", value: "aws"},{name: "cloudAccountId", value: "0123456789"}]`
            List of filter names: organizationalUnitId, platform, type, cloudAccountId, region, network, resourceGroup.
            pagesize (int): Items per query

        Returns:
            dict: Pagination of protected assets.

        Response object:
            .. literalinclude:: schemas/ProtectedAsset.json
        """
        results = {}
        pagination = {"pageSize": pagesize, "filter": {"fields": filters, 'freeTextPhrase': textSearch}}
        rsp = self._post(route='protected-asset/search', payload=pagination)
        results = rsp

        self.list_protected_assets()

        while rsp['searchAfter']:
            pagination['searchAfter'] = rsp['searchAfter']
            rsp = self._post(route='protected-asset/search', payload=pagination)
            results['assets'].extend(rsp['assets'])

        return results

    # ------------------ Rulesets ------------------
    # ----------------------------------------------

    def list_rulesets(self):
        """List Compliance Rulesets

        Returns:
            list: List of Compliance rulesets.

        Response object:
            .. literalinclude:: schemas/ComplianceRuleset.json
        """
        return self._get(route='CompliancePolicy')

    def get_ruleset(self, rulesetId=None, name=None):
        """Get a specific Compliance ruleset

        Args:
            id (str): Locate ruleset by id
            name (str): Locate ruleset by name

        Returns:
            dict: Compliance ruleset.

        Response object:
            .. literalinclude:: schemas/ComplianceRuleset.json
        """
        if id:
            return self._get(route='CompliancePolicy/%s' % str(rulesetId))
        elif name:
            return filter(lambda x: x['name'] == name, self.list_rulesets())[0]

    def create_ruleset(self, ruleset):
        """Create a Compliance ruleset

        Args:
            ruleset (dict): Ruleset object.

        Returns:
            dict: Compliance ruleset.

        Response object:
            .. literalinclude:: schemas/ComplianceRuleset.json
        """
        return self._post(route='CompliancePolicy', payload=ruleset)

    def update_ruleset(self, ruleset):
        """Update a Compliance ruleset

        Args:
            ruleset (dict): Ruleset object.

        Returns:
            dict: Compliance ruleset.

        Response object:
            .. literalinclude:: schemas/ComplianceRuleset.json
        """
        return self._put(route='CompliancePolicy', payload=ruleset)

    def delete_ruleset(self, rulesetId):
        """Delete a Compliance ruleset

        Args:
            id (int): ID of the ruleset

        Returns:
            bool: Deletion status
        """
        return self._delete(route='CompliancePolicy/%s' % str(rulesetId))

    # ------------------ Remediations ------------------
    # --------------------------------------------------

    def list_remediations(self):
        """List Remediations

        Returns:
            list: List of Remediation object.

        Response object:
            .. literalinclude:: schemas/Remediation.json
        """
        return self._get(route='ComplianceRemediation')

    def create_remediation(self, remediation):
        """Create a Remediation

        Args:
            remediation (dict): Remediation object.

        Returns:
            dict: Remediation object.

        Response object:
            .. literalinclude:: schemas/Remediation.json
        """
        return self._post(route='ComplianceRemediation', payload=remediation)

    def update_remediation(self, remediation):
        """Update a Remediation

        Args:
            remediation (dict): Remediation object.

        Returns:
            dict: Remediation object.

        Response object:
            .. literalinclude:: schemas/Remediation.json
        """
        return self._put(route='ComplianceRemediation', payload=remediation)

    def delete_remediation(self, remediationId):
        """Delete a Remediation

        Args:
            id (str): ID of the remediation

        Returns:
            bool: Deletion status
        """
        return self._delete(route='ComplianceRemediation/%s' % str(remediationId))

    # ------------------  Exclusions  ------------------
    # --------------------------------------------------

    def list_exclusions(self):
        """List all exclusions

        Returns:
            list: List of Exclusion object.

        Response object:
            .. literalinclude:: schemas/Exclusion.json
        """
        return self._get(route='Exclusion')

    def delete_exclusion(self, exclusionId):
        """Delete an exclusion

        Args:
            id (str): Id of the exclusion

        Returns:
            bool: Deletion status
        """
        return self._delete(route='Exclusion/%s' % str(exclusionId))

    # ------------------ Assessments  ------------------
    # --------------------------------------------------

    def run_assessment(self, rulesetId, cloudAccountId, region=None):
        """Run compliance assessments on Cloud Accounts, and get the results

        Args:
            rulesetId (int): Id of the Compliance Policy Ruleset to run
            cloudAccountId (str): Id of the Cloud Account
            region (str, optional): Set a specific region. Defaults to None.

        Returns:
            dict: Assessment result. Ref: /docs/source/schemas/AssessmentResults.json

        Response object:
            .. literalinclude:: schemas/AssessmentResult.json
        """
        bundle = {
            'id': rulesetId,
            'CloudAccountId': cloudAccountId
        }
        if region:
            bundle['region'] = region
        results = self._post(route='assessment/bundleV2', payload=bundle)
        return results

    def get_assessment(self, assessmentId):
        """Get results of an assesment by id

        Args:
            assessmentId (int): Report/Assessment id

        Returns:
            dict: Assesment result. Ref: /docs/source/schemas/AssessmentResults.json

        Response object:
            .. literalinclude:: schemas/AssessmentResult.json
        """
        return self._get(route='AssessmentHistoryV2/%s' % str(assessmentId))

    # -------------------- Users --------------------
    # ----------------------------------------------

    def list_users(self):
        """List all Dome9 users for the Dome9 account

        Returns:
            dict: User object. Ref: /docs/source/schemas/User.json

        Response object:
            .. literalinclude:: schemas/User.json
        """
        return self._get(route='user')

    def get_user(self, userId):
        """Get user registered in Dome9

        Args:
            userid (id): Id of the user

        Returns:
            dict: User object. Ref: /docs/source/schemas/User.json

        Response object:
            .. literalinclude:: schemas/User.json
        """
        return self._get(route='user/%s' % str(userId))

    def create_user(self, email, name, surname=""):
        """Create user in Dome9

        Args:
            email (str): User email of the new user
            name (str): Name of the new user
            surname (str, optional): Surname of the new user. Defaults to ""

        Returns:
            dict: User object. Ref: /docs/source/schemas/User.json

        Response object:
            .. literalinclude:: schemas/User.json
        """
        payload = {
            "id": None,
            "email": email,
            "firstName": name,
            "lastName": surname,
            "roleIds": [], "ssoEnabled": False,
            "permissions": {
                "access": [], "manage": [], "view": [], "create": [], "crossAccountAccess": [],
                "rulesets": [], "notifications": [], "policies": [], "alertActions": [], "onBoarding": []
                }
            }
        return self._post(route='user', payload=payload)

    def delete_user(self, userId):
        """Delete a user in Dome9

        Args:
            userid (int): Id of the user

        Returns:
            bool
        """
        return self._delete(route='user/%s' % str(userId))
