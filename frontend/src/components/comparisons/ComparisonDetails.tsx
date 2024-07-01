import React, { useState } from "react";
import {
  Box,
  Heading,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Button,
  useToast,
} from "@chakra-ui/react";
import { UserJobPostingComparison } from "../../client/models";
import { PdfDisplay } from "../Common/PdfDisplay";
import WorkExperienceDisplay from "./WorkExperienceDisplay";
import CoverLetterParagraphDisplay from "./CoverLetterParagraphDisplay";
import ModelTemperatureSelector from "../Common/ModelTemperatureSelector";
import { UserComparisonServices } from "../../client/services";

interface ComparisonDetailsProps {
  comparison: UserJobPostingComparison;
  onComparisonUpdate: (updatedComparison: UserJobPostingComparison) => void;
}

const ComparisonDetails: React.FC<ComparisonDetailsProps> = ({
  comparison,
  onComparisonUpdate,
}) => {
  const [model, setModel] = useState<string>("");
  const [temperature, setTemperature] = useState<number>(0.5);
  const [isGeneratingResume, setIsGeneratingResume] = useState(false);
  const [isGeneratingCoverLetter, setIsGeneratingCoverLetter] = useState(false);
  const toast = useToast();

  const handleGenerateResume = () => {
    setIsGeneratingResume(true);
    UserComparisonServices.generateComparisonResume(
      { comparison_id: comparison.id },
      {
        name: model,
        temperature: temperature,
      }
    )
      .then((response) => {
        toast({
          title: "Resume Generated",
          description: response.message,
          status: "success",
          duration: 3000,
          isClosable: true,
        });
        refreshComparisonData();
      })
      .catch((error) => {
        console.error("Error generating resume:", error);
        toast({
          title: "Error",
          description: "Failed to generate resume",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      })
      .finally(() => {
        setIsGeneratingResume(false);
      });
  };

  const handleGenerateCoverLetter = () => {
    setIsGeneratingCoverLetter(true);
    UserComparisonServices.generateComparisonCoverLetter(
      { comparison_id: comparison.id },
      {
        name: model,
        temperature: temperature,
      }
    )
      .then((response) => {
        toast({
          title: "Cover Letter Generated",
          description: response.message,
          status: "success",
          duration: 3000,
          isClosable: true,
        });
        refreshComparisonData();
      })
      .catch((error) => {
        console.error("Error generating cover letter:", error);
        toast({
          title: "Error",
          description: "Failed to generate cover letter",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      })
      .finally(() => {
        setIsGeneratingCoverLetter(false);
      });
  };

  const refreshComparisonData = () => {
    UserComparisonServices.getUserComparison({
      comparison_id: comparison.id,
      job_posting_id: null,
    })
      .then((updatedComparison) => {
        onComparisonUpdate(updatedComparison as UserJobPostingComparison);
      })
      .catch((error) => {
        console.error("Error refreshing comparison data:", error);
        toast({
          title: "Error",
          description: "Failed to refresh comparison data",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      });
  };

  return (
    <Box p={4}>
      <Heading as="h1" size="xl" mb={4}>
        {comparison.title}
      </Heading>
      <Text fontSize="lg" mb={2}>
        {comparison.company}
      </Text>
      <Text fontSize="md" color="gray.600" mb={4}>
        {comparison.location ?? "Unknown Location"}
      </Text>

      <ModelTemperatureSelector
        model={model}
        setModel={setModel}
        temperature={temperature}
        setTemperature={setTemperature}
      />

      <Tabs>
        <TabList>
          <Tab>Resume</Tab>
          <Tab>Cover Letter</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <Box mb={4}>
              {comparison.resume ? (
                <>
                  <Button
                    onClick={handleGenerateResume}
                    mb={4}
                    isLoading={isGeneratingResume}
                    loadingText="Regenerating..."
                  >
                    Regenerate Resume
                  </Button>
                  <PdfDisplay
                    base64String={comparison.resume}
                    fileName={`${comparison.title}_${comparison.company}_Resume.pdf`}
                  />
                </>
              ) : (
                <>
                  <Text>No resume available</Text>
                  <Button
                    onClick={handleGenerateResume}
                    mb={4}
                    isLoading={isGeneratingResume}
                    loadingText="Generating..."
                  >
                    Generate Resume
                  </Button>
                </>
              )}
            </Box>
            <Box>
              <Heading as="h3" size="sm" mb={2}>
                Work Experiences
              </Heading>
              <WorkExperienceDisplay
                experiences={comparison.work_experiences}
                onUpdate={refreshComparisonData}
              />
            </Box>
          </TabPanel>
          <TabPanel>
            <Box mb={4}>
              {comparison.cover_letter ? (
                <>
                  <Button
                    onClick={handleGenerateCoverLetter}
                    mb={4}
                    isLoading={isGeneratingCoverLetter}
                    loadingText="Regenerating..."
                  >
                    Regenerate Cover Letter
                  </Button>
                  <PdfDisplay
                    base64String={comparison.cover_letter}
                    fileName={`${comparison.title.replace(/\s+/g, '')}_${comparison.company.replace(/\s+/g, '')}_cover_letter.pdf`}
                  />
                </>
              ) : (
                <>
                  <Text>No cover letter available</Text>
                  <Button
                    onClick={handleGenerateCoverLetter}
                    mb={4}
                    isLoading={isGeneratingCoverLetter}
                    loadingText="Generating..."
                  >
                    Generate Cover Letter
                  </Button>
                </>
              )}
            </Box>
            <Box>
              <Heading as="h3" size="sm" mb={2}>
                Cover Letter Paragraphs
              </Heading>
              <CoverLetterParagraphDisplay
                paragraphs={comparison.cover_letter_paragraphs}
                onUpdate={refreshComparisonData}
              />
            </Box>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default ComparisonDetails;
