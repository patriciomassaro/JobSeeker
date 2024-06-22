import React from "react";
import { List, ListItem, Text } from "@chakra-ui/react";
import { JobPostings, JobPosting } from "../../client/models"

interface JobListProps {
  jobPostings: JobPostings;
  onJobSelect: (job: JobPosting) => void;
}
const JobList: React.FC<JobListProps> = ({ jobPostings, onJobSelect }) => {
  return (
    <List spacing={3}>
      {jobPostings.data.map((job: JobPosting) => (
        <ListItem key={job.id} onClick={() => onJobSelect(job)} cursor="pointer" p={2} _hover={{ bg: "gray.100" }}>
          <Text fontWeight="bold"> {job.title}</Text>
          <Text>{job.company}</Text>
          <Text>{job.location ?? "Unknown Location"}</Text>
        </ListItem>
      ))}
    </List>
  );
};

export default JobList;
