import logging
from rest_requests import RestRequests
import time

LOG = logging.getLogger("flask_ask").setLevel(logging.DEBUG)

server_ip = '10.60.136.184'  # ip of the Unisphere server to query
port = '8443'  # port to connect to the unisphere server on, e.g. 8443
username, password = 'smc', 'smc'  # credentials for the Unisphere server

base_url = 'https://%s:%s/univmax/restapi' % (server_ip, port)
vmax_req = RestRequests(username, password, False, None, base_url)

# HTTP constants
GET = 'GET'
POST = 'POST'
PUT = 'PUT'
DELETE = 'DELETE'


def check_status_code_success(status_code, response):
    """Check if a status code indicates success.

    :param status_code: the status code
    :param response: the server response
    """
    if status_code not in [200, 201, 202, 204]:
        print('Error making rest call.')
        print(response)
        raise Exception


def get_array_list():
    """Returns a list of arrays.

    :return: array list
    """
    target_uri = "/84/wlp/symmetrix"
    response, status_code = vmax_req.rest_request(target_uri, GET)
    check_status_code_success(status_code, response)
    try:
        array_list = response['symmetrixId']
    except KeyError:
        array_list = []
    return array_list


def get_alert_summary(array):
    """Get a summary of alerts for a specified array.
    
    :param array: the array serial number
    :return: summary of alert information
    """
    perf_unacknowledged, array_unacknowledged, server_unacknowledged = 0, 0, 0
    target_uri = "/84/system/alert_summary"
    response, status_code = vmax_req.rest_request(target_uri, GET)
    check_status_code_success(status_code, response)
    server_unacknowledged = response['serverAlertSummary']['all_unacknowledged_count']
    symm_alert_list = response['symmAlertSummary']
    for symm_alert in symm_alert_list:
        if symm_alert['symmId'] == array:
            perf_unacknowledged = symm_alert['performanceAlertSummary']['all_unacknowledged_count']
            array_unacknowledged = symm_alert['arrayAlertSummary']['all_unacknowledged_count']
    return perf_unacknowledged, array_unacknowledged, server_unacknowledged


def get_all_array_alerts(array, filters=None):
    """Queries for a list of All Alert ids for the given array.

    Optionally can be filtered by: create_date_milliseconds(=<>),
    description(=<>), type, severity, state, created_date, acknowledged.
    :param array: the array serial number
    :param filters: dict of filters - optional
    :return: list of alert ids
    """
    target_uri = "/84/system/symmetrix/%(array)s/alert" % {'array': array}
    response, status_code = vmax_req.rest_request(target_uri, GET, filters)
    check_status_code_success(status_code, response)
    return response['alertId']


def get_all_sg_compliance(array, filters=None):
    target_uri = "/84/sloprovisioning/symmetrix/%(array)s/" % {'array': array}
    response, status_code = vmax_req.rest_request(target_uri, 'get', filters)
    return response['sloCompliance']


def get_processing_job(array, jobId, filters=None):
    target_uri = "/84/system/symmetrix/%(array)s/job/%(jobId)s" % {'array': array, 'jobId': jobId}
    response, status_code = vmax_req.rest_request(target_uri, 'get', filters)
    return response['task']


def get_alert(array, alert_id):
    """Queries for a particular alert.

    :param array: the array serial number
    :param alert_id: specific id of the alert - optional
    :return: dict, status_code
    """
    target_uri = "/84/system/symmetrix/%s/alert/%s" % (array, alert_id)
    response, status_code = vmax_req.rest_request(target_uri, GET)
    check_status_code_success(status_code, response)
    try:
        description = response['description']
        created_date = response['created_date']
    except KeyError:
        description, created_date = "Unknown", "Unknown"
    alert_desc = ("Alert description is %(desc)s. The alert was created on "
                  "%(date)s" % {'desc': description, 'date': created_date})
    return alert_desc


def acknowledge_array_alert(array, alert_id):
    """Acknowledge a specified alert.

    Acknowledge is the only "PUT" (edit) option available.
    :param array: the array serial number
    :param alert_id: the alert id - string
    :return: dict, status_code
    """
    target_uri = ("/84/system/symmetrix/%s/alert/%s" %
                  (array, alert_id))
    payload = {"editAlertActionParam": "ACKNOWLEDGE"}
    response, status_code = vmax_req.rest_request(target_uri, PUT,
                                                  request_object=payload)
    check_status_code_success(status_code, response)


def delete_alert(array, alert_id):
    """Delete a specified alert.

    :param array: the array serial number
    :param alert_id: the alert id - string
    :return: None, status code
    """
    target_uri = ("/84/system/symmetrix/%s/alert/%s" %
                  (array, alert_id))
    return vmax_req.rest_request(target_uri, DELETE)


def get_symm_capacity(array, filters=None):
    target_uri = "/84/sloprovisioning/symmetrix/%(array)s/srp/SRP_1" \
                 % {'array': array}
    response, status_code = vmax_req.rest_request(target_uri, 'get', filters)
    return response['effective_used_capacity_percent']


def add_new_volume_to_sg(
        array, volume_name, storagegroup_name, volume_size):
    """Create a new volume in the given storage group.

    :param array: the array serial number
    :param volume_name: the volume name (String)
    :param storagegroup_name: the storage group name
    :param volume_size: volume size (String)
    :returns: dict -- volume_dict - the volume dict
    """
    payload = (
        {"executionOption": "ASYNCHRONOUS",
         "editStorageGroupActionParam": {
             "expandStorageGroupParam": {
                 "addVolumeParam": {
                     "num_of_vols": 1,
                     "emulation": "FBA",
                     "volumeIdentifier": {
                         "identifier_name": volume_name,
                         "volumeIdentifierChoice": "identifier_name"},
                     "volumeAttribute": {
                         "volume_size": volume_size,
                         "capacityUnit": "GB"}}}}})
    job = modify_storage_group(array, storagegroup_name, payload)
    try:
        job_id = job['jobId']
    except (KeyError, ValueError):
        job_id = None

    return job_id


def modify_storage_group(array, storagegroup_name, payload):
    """
    
    :param array: 
    :param storagegroup_name: 
    :param payload: 
    :return: 
    """
    url = ("/84/sloprovisioning/symmetrix/%(array)s/storagegroup/%(sg_name)s"
           % {'array': array, 'sg_name': storagegroup_name})
    job, status_code,  = vmax_req.rest_request(url, PUT,
                                               request_object=payload)
    check_status_code_success(status_code, job)
    return job

def get_host_list(array):
    """
    
    :param array: 
    :return: 
    """
    host_list = None
    url = "/84/sloprovisioning/symmetrix/%(array)s/host" % {'array': array}
    host, status_code = vmax_req.rest_request(url, GET)
    if not status_code == 404:
        try:
            host_list = host['hostId']
        except KeyError:
            pass
    return host_list


def get_storage_group(array, storagegroup_name):
    """
    
    :param array: 
    :param storagegroup_name: 
    :return: 
    """
    url = ("/84/sloprovisioning/symmetrix/%(array)s/storagegroup/%(sg_name)s"
           % {'array': array, 'sg_name': storagegroup_name})
    response, status_code = vmax_req.rest_request(url, GET)
    if status_code == 404:
        return None
    return response


def get_host_masking_view(array, host, size):
    """
    
    :param array: 
    :param host: 
    :return: 
    """
    mv_name = None
    sg_name = None
    job_id = None
    url = ("/84/sloprovisioning/symmetrix/%(array)s/host/%(host)s"
           % {'array': array, 'host': host})
    host_details, status_code = vmax_req.rest_request(url, GET)
    check_status_code_success(status_code, host_details)
    try:
        mv_list = host_details['maskingview']
        if mv_list:
            mv_name = mv_list[0]
            sg_name = get_storage_group_from_masking_view(array, mv_name)
    except (KeyError, IndexError):
        mv_name = "%(host)s_alexa_MV" % {'host': host}
        sg_name, job_id = create_masking_view(array, mv_name, host, vol_size=size)
    return mv_name, sg_name, job_id


def get_storage_group_from_masking_view(array, mv_name):
    sg_name = None
    url = ("/84/sloprovisioning/symmetrix/%(array)s/maskingview/%(mv_name)s"
           % {'array': array, 'mv_name': mv_name})
    mv_details, status_code = vmax_req.rest_request(url, GET)
    try:
        sg_name = mv_details['storageGroupId']
    except KeyError:
        pass
    return sg_name


def create_masking_view(array, mv_name, host, vol_size=None):
    """
    
    :param array: 
    :param mv_name: 
    :param host: 
    :return: 
    """
    sg_name = "%(mv_name)s_SG" % {'mv_name': mv_name}
    sg_details = get_storage_group(array, sg_name)
    print(sg_details)
    if sg_details is None:
        create_storage_group(array, sg_name, vol_size)
    pg_name = "alexa_pg"
    payload = {
        "executionOption": "ASYNCHRONOUS",
        "portGroupSelection": {
        "useExistingPortGroupParam": {"portGroupId": pg_name}},
        "maskingViewId": mv_name,
        "hostOrHostGroupSelection": {"useExistingHostParam": {
            "hostId": host}},
        "storageGroupSelection": {"useExistingStorageGroupParam": {
            "storageGroupId": sg_name}}}
    url = ("/84/sloprovisioning/symmetrix/%(array)s/maskingview"
           % {'array': array})
    job, status_code = vmax_req.rest_request(url, POST, request_object=payload)
    check_status_code_success(status_code, job)
    try:
        job_id = job['jobId']
    except (KeyError, ValueError):
        job_id = None
    return sg_name, job_id


def create_storage_group(array, sg_name, size):
    """
    
    :param array: 
    :param sg_name: 
    :param size:
    :return: 
    """
    url = ("/84/sloprovisioning/symmetrix/%(array)s/storagegroup"
           % {'array': array})
    payload = {"srpId": "SRP_1",
               "storageGroupId": sg_name,
               "emulation": "FBA",
               "sloBasedStorageGroupParam": [
                   {
                       "noCompression": 'false',
                       "num_of_vols": 1,
                       "sloId": "Diamond",
                       "workloadSelection": "None",
                       "volumeIdentifier": {
                           "volumeIdentifierChoice": "none"
                       },
                       "volumeAttribute": {
                           "volume_size": size,
                           "capacityUnit": "GB"}}],
               "create_empty_storage_group": 'false'
}
    job, status_code = vmax_req.rest_request(
        url, POST, request_object=payload)
    check_status_code_success(status_code, job)

def provision_storage_to_host(array, host, size):
    """
    
    :param array: 
    :param host: 
    :param size: 
    :return: 
    """
    volume_name = "alexa_vol_%(time)s" % {'time': str(time.time())}
    mv_name, sg_name, job_id = get_host_masking_view(array, host, size)
    if not job_id:
        job_id = add_new_volume_to_sg(
            array, volume_name, sg_name, str(size))
    return job_id

def get_array_metrics(array_id):
    """Get array metrics.
    Get all avaliable performance statistics for specified time 
    period return in JSON
    :param start_date: EPOCH Time
    :param end_date: Epoch Time
    :return: array_results_combined
    """
    start_date= 1495023300000
    end_date=1495023300000
    target_uri = "/performance/Array/metrics"
    array_perf_payload = {
        'symmetrixId': array_id,
        'endDate': end_date,
        'dataFormat': 'Average',
        'metrics': [
            'HostIOs', 'HostMBs', 'PercentCacheWP',
            'ReadResponseTime', 'InfoAlertCount', 'WarningAlertCount', 'CriticalAlertCount',
            'FE_Balance',
            'DA_Balance'
        ],
        'startDate': start_date
    }
    array_perf_data = vmax_req.rest_request(
        target_uri, POST, request_object=array_perf_payload)
    return array_perf_data[0]['resultList']['result'][0]