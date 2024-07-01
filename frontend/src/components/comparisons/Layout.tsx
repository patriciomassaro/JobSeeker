import React, { useEffect, useState } from "react";
import { Container, Flex, Box, Text } from "@chakra-ui/react";
import ComparisonList from "./ComparisonList";
import { UserComparisonServices } from "../../client/services";
import { UserJobPostingComparison, UserJobPostingComparisons } from "../../client/models";
import ComparisonDetails from "./ComparisonDetails";

const MainLayout: React.FC = () => {
  const [jobComparisons, setJobComparisons] = useState<UserJobPostingComparisons | null>(null);
  const [selectedJobComparison, setSelectedJobComparison] = useState<UserJobPostingComparison | null>(null);

  useEffect(() => {
    const fetchComparisons = async () => {
      try {
        const response = await UserComparisonServices.getUserComparisons();
        setJobComparisons(response);
      } catch (error) {
        console.error("Error fetching job comparisons:", error);
      }
    };

    fetchComparisons();
  }, []);

  const handleJobComparisonSelect = (comparison: UserJobPostingComparison): void => {
    const fetchJobDetails = async () => {
      try {
        const response = await UserComparisonServices.getUserComparison({
          comparison_id: comparison.id,
          job_posting_id: null
        });
        setSelectedJobComparison(response as UserJobPostingComparison);
      } catch (error) {
        console.error("Error fetching job comparison:", error);
      }
    };
    fetchJobDetails();
  };

  const handleComparisonUpdate = (updatedComparison: UserJobPostingComparison) => {
    setSelectedJobComparison(updatedComparison);
    // Also update the comparison in the list if necessary
    if (jobComparisons) {
      const updatedComparisons = {
        ...jobComparisons,
        data: jobComparisons.data.map(comp =>
          comp.id === updatedComparison.id ? updatedComparison : comp
        )
      };
      setJobComparisons(updatedComparisons);
    }
  };

  return (
    <Container maxW="full">
      <Flex height="100vh">
        <Box width="20%" overflowY="scroll" borderRight="1px solid #ccc">
          {jobComparisons && (
            <ComparisonList jobComparisons={jobComparisons} onComparisonSelect={handleJobComparisonSelect} />
          )}
        </Box>
        <Box width="80%" p={2}>
          {selectedJobComparison ? (
            <ComparisonDetails
              comparison={selectedJobComparison}
              onComparisonUpdate={handleComparisonUpdate}
            />
          ) : (
            <Text>Select a job to see details</Text>
          )}
        </Box>
      </Flex>
    </Container>
  );
};

export default MainLayout;
