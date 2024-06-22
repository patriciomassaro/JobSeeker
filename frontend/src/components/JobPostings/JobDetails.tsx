
import React from 'react';
import { Box, Text, Heading } from '@chakra-ui/react';
import { JobPosting } from '../../client/models';

interface JobDetailsProps {
  job: JobPosting;
}

const JobDetails: React.FC<JobDetailsProps> = ({ job }) => {

  const formatDescription = (description: string) => {
    return description.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        <br />
      </React.Fragment>
    ));
  };


  return (
    <Box>
      <Heading size="lg">{job.title}</Heading>
      <Text fontWeight="bold">{job.company}</Text>
      <Text>{job.location ?? 'Location not specified'}</Text>
      <Text mt={4}>{formatDescription(job.description)}</Text>
      <Box mt={4}>
        <Text fontWeight="bold">Seniority Level:</Text>
        <Text>{job.seniority_level ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Employment Type:</Text>
        <Text>{job.employment_type ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Experience Level:</Text>
        <Text>{job.experience_level ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Remote Modality:</Text>
        <Text>{job.remote_modality ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Salary Range:</Text>
        <Text>{job.salary_range ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">About the Company:</Text>
        <Text>{job.institution_about ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Website:</Text>
        <Text>{job.institution_website ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Industry:</Text>
        <Text>{job.institution_industry ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Company Size:</Text>
        <Text>{job.institution_size ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Followers:</Text>
        <Text>{job.institution_followers ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Employees:</Text>
        <Text>{job.institution_employees ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Tagline:</Text>
        <Text>{job.institution_tagline ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Location:</Text>
        <Text>{job.institution_location ?? 'Not specified'}</Text>
      </Box>
      <Box mt={4}>
        <Text fontWeight="bold">Specialties:</Text>
        <Text>{job.institution_specialties?.join(', ') ?? 'Not specified'}</Text>
      </Box>
    </Box>
  );
};

export default JobDetails;
