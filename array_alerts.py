import logging
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
import vmax_requests as vmax

app = Flask(__name__)
ask = Ask(app, "/")
LOG = logging.getLogger("flask_ask").setLevel(logging.DEBUG)

@ask.launch
def new_game():
    arrays = vmax.get_array_list()
    session.attributes['arrays'] = arrays
    session.attributes['job_ids'] = []
    if len(arrays) == 1:
        session.attributes['array'] = arrays[0]
    welcome_msg = render_template('welcome')
    return question(welcome_msg)


@ask.intent("SymmCapacityIntent")
def get_symm_capcity():
    array = session.attributes['array']
    effective_used_capacity_percent = vmax.get_symm_capacity(array)
    msg = render_template('total_usable_capacity', effective_used_capacity_percent=effective_used_capacity_percent)
    return question(msg)


@ask.intent("VmaxIntroIntent")
def vmax_intro():
    vmax_message = render_template('vmax_intro')
    return question(vmax_message)


@ask.intent("ListArraysIntent")
def list_arrays():
    arrays = vmax.get_array_list()
    len_array_list = len(arrays)
    if len_array_list == 1:
        session.attributes['array'] = arrays[0]
        arrays_msg = render_template('one_array', amount=len_array_list,
                                     array=arrays[0])
    else:
        arrays_msg = render_template('array', amount=len_array_list,
                                     array_list=list(enumerate(arrays)))
    session.attributes['arrays'] = arrays
    return question(arrays_msg)


@ask.intent("SelectArrayIntent", convert={'id': int})
def select_array(id):
    array_list = session.attributes['arrays']
    for array in array_list:
        if array.endswith(str(id)):
            session.attributes['array'] = array
            msg = render_template('found_array', symm_id=array)
            break
    else:
        msg = render_template('no_array', symm_id=str(id))
    return question(msg)


@ask.intent("ListAlertsIntent", convert={'id': int})
def array_alerts(id=None):
    array_id = None
    if id:
        array_list = session.attributes['arrays']
        for array in array_list:
            if array.endswith(str(id)):
                array_id = array
    else:
        array_id = session.attributes['array']
    (perf_unacknowledged, array_unacknowledged,
     server_unacknowledged) = vmax.get_alert_summary(array_id)
    total_unacknowledged = perf_unacknowledged + array_unacknowledged + server_unacknowledged
    if total_unacknowledged:
        msg = render_template('alerts', array_alert_num=total_unacknowledged,
                              server_unacknowledged=server_unacknowledged)
    else:
        msg = render_template('no_alerts')
    return question(msg)


@ask.intent("ListSGComplianceIntent")
def list_sg_compliance():
    array = session.attributes['array']
    sg_compliance_list = vmax.get_all_sg_compliance(array)
    # print(type(sg_compliance_list))
    # for v in sg_compliance_list:
    #     print(v)
    #     print(int(sg_compliance_list[v]))
    all_sg_count = sum([int(sg_compliance_list[v]) for v in sg_compliance_list])

    if sg_compliance_list and len(sg_compliance_list) > 0:
        msg = render_template('compliance_details', all_sg_count=all_sg_count,
                              stable_sg_count=sg_compliance_list['slo_stable'],
                              marginal_sg_count=sg_compliance_list['slo_marginal'],
                              critical_sg_count=sg_compliance_list['slo_critical'],
                              no_slo_count=sg_compliance_list['no_slo'])
        return question(msg)


@ask.intent("ListProcessingJob")
def list_processing_jobs():
    job_ids = []
    task_descriptions = []
    array = session.attributes['array']
    if session.attributes.get('job_ids'):
        job_ids = session.attributes['job_ids']
    jobs_processing_list = []

    for job in job_ids:
        tasks, status = vmax.get_processing_job(array, job)
        job_task_status_tuple = (job, tasks[0], status)
        jobs_processing_list.append(job_task_status_tuple)

    if jobs_processing_list:
        msg = render_template('processing_jobs_details',
                              jobs_processing_count=len(jobs_processing_list),
                              processing_jobs_list=str(jobs_processing_list[0][1]),
                              status=str(jobs_processing_list[0][2]))
    else:
        msg = render_template('no_jobs')
    return question(msg)


@ask.intent("GetAlertDetailsIntent")
def list_and_acknowledge_alerts():
    return_alerts = []
    array = session.attributes['array']
    alert_list = vmax.get_all_array_alerts(
        array, filters={'acknowledged': 'false'})
    if alert_list and len(alert_list) > 0:
        for alert_id in alert_list:
            alert_details = vmax.get_alert(array, alert_id)
            return_alerts.append(alert_details)
            vmax.acknowledge_array_alert(array, alert_id)
    msg = render_template('alert_details',
                          alert_list=list(enumerate(return_alerts)))
    return question(msg)


@ask.intent("ProvisionStorageIntent")
def return_host_list():
    array = session.attributes['array']
    host_list = vmax.get_host_list(array)
    if host_list and len(host_list) > 0:
        msg = render_template(
            'host_list', host_count=len(host_list),
            host_list=list(enumerate(host_list)))
    else:
        msg = render_template('no_hosts')
    return question(msg)


@ask.intent("ChooseHostIntent", convert={'size': int})
def provision_to_host(size):
    array = session.attributes['array']
    host = 'test-demo'
    job_id = vmax.provision_storage_to_host(array, host, size)
    session.attributes['job_ids'].append(job_id)
    msg = render_template('provision_storage', host=host, size=size)
    return question(msg)


@ask.on_session_started
def new_session():
    LOG.info('new session started')

@ask.intent("whatcanido")
def wcid():
    wcid_msg = render_template('what_can_i_do')
    return question(wcid_msg)

@ask.intent("snapresourcesIntent")
def snap_resource_faq():
    snap_resource_msg = render_template('snap_resources')
    return question(snap_resource_msg)

@ask.intent("snapdefinitionIntent")
def snap_definition_faq():
    snap_definition_msg = render_template('snapvx_definition')
    return question(snap_definition_msg)

@ask.intent("snapdefinedIntent")
def snap_defined_faq():
    snap_defined_faq_msg = render_template('defined_meaning')
    return question(snap_defined_faq_msg)

@ask.intent("snapunmountIntent")
def snap_unmount_faq():
    snap_unmount_faq_msg = render_template('unmount_link')
    return question(snap_unmount_faq_msg)

@ask.intent("snaprescanIntent")
def snap_rescan_faq():
    snap_rescan_faq_msg = render_template('rescan_volumes')
    return question(snap_rescan_faq_msg)

@ask.intent("alertshelp")
def alert_help():
    alert_help_msg = render_template('alert_help')
    return question(alert_help_msg)

@ask.intent("provisioninghelp")
def provisioning_help():
    provisioning_help_msg = render_template('provisioning_help')
    return question(provisioning_help_msg)

@ask.intent("faq_help")
def faq_help():
    faq_help_msg = render_template('faq_help')
    return question (faq_help_msg)

@ask.intent("vmaxlimits")
def vmax_limits_faq():
    vmax_limits_msg = render_template('vmax_device_limits')
    return question(vmax_limits_msg)

@ask.intent("vmaxninefifty")
def vmax_950_faq():
    vmax_950_msg = render_template('vmax_950')
    return question(vmax_950_msg)

@ask.intent("ndmdefinition")
def ndm_definition_faq():
    ndm_definition_msg = render_template('ndm_definition')
    return question(ndm_definition_msg)

@ask.intent("GoodbyeIntent")
def goodbye():
    return statement(render_template('goodbye'))

@ask.intent("DestroyArray")
def destroy_array():
    return question(render_template('destroy_array'))

#performance_stats Your VMAX system is running {{HostIOs}} totaling {{HostMBs}} megabytes per second.  Cach Utilization
                  #is at {{PercentCacheWP}} and your average read response time is {{ReadResponseTime}} milliseconds.

@ask.intent("perfstats")
def perf_stats():
    array_id=session.attributes['array']
    perf_stats = vmax.get_array_metrics(array_id)
    msg = render_template('performance_stats', HostIOs = round (perf_stats['HostIOs']),HostMBs = round(perf_stats['HostMBs']),PercentCacheWP = round (perf_stats['PercentCacheWP']),ReadResponseTime=perf_stats['ReadResponseTime'])
    return question (msg)
if __name__ == '__main__':
    app.run(debug=True)
