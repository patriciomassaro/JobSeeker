import { useState, useEffect } from "react";
import {
  Container,
  Heading,
  Box,
  ChakraProvider,
  Flex,
  Text,
  Input,
  Button,
  VStack,
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { JobPostingServices, UserComparisonServices } from "../../client/services";
import { JobPostings, JobPosting, UserJobPostingComparison, Message } from "../../client/models";
import JobList from "../../components/JobPostings/JobList";
import JobDetails from "../../components/JobPostings/JobDetails";
import Pagination from "../../components/JobPostings/Pagination"


export const Route = createFileRoute("/_layout/jobpostings")({
  component: JobPostingsHome,
});

function JobPostingsHome() {
  const [selectedJob, setSelectedJob] = useState<JobPosting | null>(null);
  const [jobPostings, setJobPostings] = useState<JobPostings | null>(null);
  const [jobTitle, setJobTitle] = useState<string>("");
  const [companyName, setCompanyName] = useState<string>("");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [userComparison, setUserComparison] = useState<UserJobPostingComparison | Message | null>(null);
  const limit = 25;

  const fetchJobPostings = async () => {
    try {
      const response = await JobPostingServices.getJobPostings({
        requestBody: {
          skip: limit * (currentPage - 1),
          limit: limit,
          job_title: jobTitle,
          company_name: companyName,
        },
      });
      setJobPostings(response);
    } catch (error) {
      console.error("Error fetching job postings:", error);
    }
  };

  const fetchComparisonStatus = async (ComparisonId: number | null = null, JobPostingId: number | null = null) => {
    if (!ComparisonId && !JobPostingId) {
      console.error("Either ComparisonId or JobPostingId must be provided");
      setUserComparison(null);
      return;
    }
    try {
      const comparison = await UserComparisonServices.getUserComparison({
        comparison_id: ComparisonId,
        job_posting_id: JobPostingId,
      });
      setUserComparison(comparison);
    } catch (error) {
      // Check if the error is an instance of Error and has a name property
      if (error instanceof Error && 'name' in error) {
        // Check if it's a 404 error
        if (error.name === 'ApiError' && (error as any).status === 404) {
          // Silently set comparison to null for 404 errors
          setUserComparison(null);
          return;
        }
      }
      // For other errors, you might want to log them or handle them differently
      console.error("Unexpected error fetching comparison status:", error);
      setUserComparison(null);
    }
  };

  useEffect(() => {
    fetchJobPostings();
  }, [currentPage, jobTitle, companyName]);

  const handleSearch = () => {
    setCurrentPage(1);
    fetchJobPostings();
  };

  const handleJobSelect = (job: JobPosting) => {
    setSelectedJob(job);
    setUserComparison(null);
    fetchComparisonStatus(null, job.id);
  };

  const handleActivateComparison = async (JobPostingId: number) => {
    try {
      // console.log("Activating comparison for job ID:", jobPostingId)

      await UserComparisonServices.activateUserComparison({ job_posting_id: JobPostingId });

      fetchComparisonStatus(null, JobPostingId); // Refresh status
    } catch (error) {
      // console.error("Error activating comparison:", error);
    }
  };

  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  }
  return (
    <ChakraProvider>
      <Container maxW="full">
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
          Job Postings
        </Heading>
        <VStack spacing={4} mb={6}>
          <Input
            placeholder="Job Title"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
          />
          <Input
            placeholder="Company Name"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
          />
          <Button onClick={handleSearch}>Search</Button>
          <Pagination
            currentPage={currentPage}
            onPageChange={handlePageChange}
            totalItems={limit * 10}
            itemsPerPage={limit}
          />

        </VStack>
        <Flex height="100vh">
          <Box width="25%" overflowY="scroll" borderRight="1px solid #ccc">
            {jobPostings && (
              <JobList
                jobPostings={jobPostings}
                onJobSelect={handleJobSelect}
              />
            )}
          </Box>
          <Box width="75%" p={2}>
            {selectedJob ? (
              <>
                <Button
                  onClick={() => handleActivateComparison(selectedJob.id)}
                  disabled={userComparison !== null && 'is_active' in userComparison && userComparison.is_active}
                  mt={4}
                >
                  {userComparison !== null && 'is_active' in userComparison && userComparison.is_active
                    ? "Comparison already active"
                    : "Activate this job for comparison"}
                </Button>

                <JobDetails job={selectedJob} />
              </>
            ) : (
              <Text>Select a job to see details</Text>
            )}
          </Box>
        </Flex>
      </Container>
    </ChakraProvider>
  );
}
