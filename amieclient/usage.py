import json
from collections import namedtuple

UsageAttributes = namedtuple('UsageAttributes',
                             ['node_count', 'cpu_core_count', 'job_name',
                              'memory', 'queue'],
                             # for named tuples, defaults start with the right,
                             # so 4 Nones here means that the last 4 fields
                             # above have a default value of None
                             defaults=[None] * 4
                             )


class ComputeUsageRecord:
    """
    A ComputeUsageRecord. A Record of Compute Usage.

    (TODO: a better description)
    """
    def __init__(self, *,
                 parent_record_id=None, queue=None, cpu_core_count=None,
                 job_name=None, memory=None, charge, end_time,
                 local_project_id, local_record_id, resource, start_time,
                 submit_time, username, node_count):
        """
        Creates a new usage record.

        Args:
            parent_record_id (str): Job ID of parent job if this record is a sub job.  Typically a slurm job id
            queue (str): Scheduler queue name the job was submitted to
            cpu_core_count (str): Number of cores used by the job
            job_name (str): Job name
            memory (str): ??? Max memory for a node?  Bytes?
            charge (str): The amount of allocation units that should be deducted from the project allocation for this job
            end_time (str): Job End Time
            local_project_id (str): The Site Project ID for the job.  This must match the ProjectID provided by the site for the project with AMIE
            local_record_id (str): Site Job ID.  Typically a slurm job id
            resource (str): Resource the job ran on.  Must match the resource name used in AMIE
            start_time (str): Start Time of the job
            submit_time (str): Start Time of the job
            username (str): The local username of the user who ran the job.  Must match the username used in AMIE
            node_count (str): Number of nodes the job ran on

        Returns:
            UsageRecord
        """

        self.attributes = UsageAttributes(node_count, cpu_core_count, job_name,
                                          memory, queue)

        self.parent_record_id = parent_record_id,
        self.charge = charge
        self.end_time = end_time
        self.local_project_id = local_project_id
        self.local_record_id = local_record_id
        self.resource = resource
        self.start_time = start_time
        self.submit_time = submit_time
        self.username = username

    @classmethod
    def from_dict(cls, input_dict):
        """
        Returns a UsageRecord from a provided dictionary
        """

        return cls(
            username=input_dict['Username'],
            local_project_id=input_dict['LocalProjectID'],
            local_record_id=input_dict['LocalRecordID'],
            resource=input_dict['Resource'],
            submit_time=input_dict['SubmitTime'],
            start_time=input_dict['StartTime'],
            end_time=input_dict['EndTime'],
            charge=input_dict['Charge'],
            node_count=input_dict['Attributes']['NodeCount'],
            cpu_core_count=input_dict['Attributes'].get('CpuCoreCount'),
            job_name=input_dict['Attributes'].get('JobName'),
            memory=input_dict['Attributes'].get('Memory'),
            queue=input_dict['Attributes'].get('Queue'),
            parent_record_id=input_dict.get('ParentRecordID'),
        )

    @classmethod
    def from_json(cls, input_json):
        """
        Returns a UsageRecord from a provided JSON string
        """
        input_dict = json.loads(input_json)
        return cls.from_dict(input_dict)

    @property
    def as_dict(self):
        """
        Returns a dictionary version of this record
        """

        # Get the attributes, skip over anything not specified
        attributes = {}
        for k, v in self.attributes._asdict().items():
            if v is not None:
                attributes[k] = v

        d = {
            'Username': self.username,
            'LocalProjectID': self.local_project_id,
            'LocalRecordID': self.local_record_id,
            'Resource': self.resource,
            'SubmitTime': self.submit_time,
            'StartTime': self.start_time,
            'EndTime': self.end_time,
            'Charge': self.charge,
            'Attributes': attributes
        }

        if self.parent_record_id is not None:
            d['ParentRecordID'] = self.parent_record_id

        return d

    @property
    def as_json(self):
        """
        Returns a json version of this record
        """

        return json.dumps(self.as_dict)


class UsageMessageException(Exception):
    """
    Exception for invalid data in a UsageMessage
    """
    pass

class UsageMessage:
    def __init__(self, usage_type, records):
        # Normalize the usage type's capitalization
        ut = usage_type.lower().capitalize()
        if ut not in ['Compute', 'Storage', 'Adjustment']:
            raise UsageMessageException(f'Invalid usage type {ut}')
        self.records = records

    @classmethod
    def from_dict(cls, input_dict):
        """
        Returns a UsageMessage from a provided dictionary
        """
        ut = input_dict['UsageType']
        records = [UsageRecord.from_dict(d) for d in input_dict['Records']]
        return cls(ut, records)

    @classmethod
    def from_json(cls, input_json):
        input_dict = json.loads(input_json)
        return cls.from_dict(input_dict)

    @property
    def as_dict(self):
        """
        Returns a dictionary version of this record
        """
        d = {
            'UsageType': self.usage_type,
            'Records': [r.as_dict for r in self.records]
        }
        return d

    @property
    def as_json(self):
        """
        Returns a json version of this message
        """
        return json.dumps(self.as_dict)

    def _chunked(self, chunk_size=1000):
        """
        Generator that yields UsageMessages with a maximum of chunk_size number
        UsageRecords. Useful for not going over the 256kb POST limit
        """
        for i in range(0, len(self.records), chunk_size):
            r = self.records[i:i+chunk_size]
            yield self.__class__(self.usage_type, r)
