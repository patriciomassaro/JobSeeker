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
  const [isGeneratingWorkExperiences, setIsGeneratingWorkExperiences] = useState(false);
  const [isGeneratingCoverLetterParagraphs, setIsGeneratingCoverLetterParagraphs] = useState(false);
  const [isBuildingResume, setIsBuildingResume] = useState(false);
  const [isBuildingCoverLetter, setIsBuildingCoverLetter] = useState(false);
  const toast = useToast();

  const handleGenerateWorkExperiences = async () => {
    setIsGeneratingWorkExperiences(true);
    try {
      const response = await UserComparisonServices.generateWorkExperiences(
        { comparison_id: comparison.id },
        { name: model, temperature: temperature }
      );
      toast({
        title: "Work Experiences Generated",
        description: response.message,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      await handleBuildResume();
    } catch (error) {
      console.error("Error generating work experiences:", error);
      toast({
        title: "Error",
        description: "Failed to generate work experiences",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsGeneratingWorkExperiences(false);
    }
  };

  const handleGenerateCoverLetterParagraphs = async () => {
    setIsGeneratingCoverLetterParagraphs(true);
    try {
      const response = await UserComparisonServices.generateCoverLetterParagraphs(
        { comparison_id: comparison.id },
        { name: model, temperature: temperature }
      );
      toast({
        title: "Cover Letter Paragraphs Generated",
        description: response.message,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      await handleBuildCoverLetter();
    } catch (error) {
      console.error("Error generating cover letter paragraphs:", error);
      toast({
        title: "Error",
        description: "Failed to generate cover letter paragraphs",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsGeneratingCoverLetterParagraphs(false);
    }
  };

  const handleBuildResume = async () => {
    setIsBuildingResume(true);
    try {
      const response = await UserComparisonServices.buildResume({ comparison_id: comparison.id });
      toast({
        title: "Resume Built",
        description: response.message,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      refreshComparisonData();
    } catch (error) {
      console.error("Error building resume:", error);
      toast({
        title: "Error",
        description: "Failed to build resume",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsBuildingResume(false);
    }
  };

  const handleBuildCoverLetter = async () => {
    setIsBuildingCoverLetter(true);
    try {
      const response = await UserComparisonServices.buildCoverLetter({ comparison_id: comparison.id });
      toast({
        title: "Cover Letter Built",
        description: response.message,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      refreshComparisonData();
    } catch (error) {
      console.error("Error building cover letter:", error);
      toast({
        title: "Error",
        description: "Failed to build cover letter",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsBuildingCoverLetter(false);
    }
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

  const handleWorkExperienceUpdate = async () => {
    await handleBuildResume();
  };

  const handleCoverLetterParagraphUpdate = async () => {
    await handleBuildCoverLetter();
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
              <Button
                onClick={handleGenerateWorkExperiences}
                mb={4}
                isLoading={isGeneratingWorkExperiences || isBuildingResume}
                loadingText={isGeneratingWorkExperiences ? "Generating..." : "Building..."}
                mr={2}
              >
                Generate Work Experiences
              </Button>
              {comparison.resume && (
                <PdfDisplay
                  base64String={comparison.resume}
                  fileName={`${comparison.title}_${comparison.company}_Resume.pdf`}
                />
              )}
            </Box>
            <Box>
              <Heading as="h3" size="sm" mb={2}>
                Work Experiences
              </Heading>
              <WorkExperienceDisplay
                experiences={comparison.work_experiences}
                onUpdate={handleWorkExperienceUpdate}
              />
            </Box>
          </TabPanel>
          <TabPanel>
            <Box mb={4}>
              <Button
                onClick={handleGenerateCoverLetterParagraphs}
                mb={4}
                isLoading={isGeneratingCoverLetterParagraphs || isBuildingCoverLetter}
                loadingText={isGeneratingCoverLetterParagraphs ? "Generating..." : "Building..."}
                mr={2}
              >
                Generate Cover Letter Paragraphs
              </Button>
              {comparison.cover_letter && (
                <PdfDisplay
                  base64String={comparison.cover_letter}
                  fileName={`${comparison.title.replace(/\s+/g, '')}_${comparison.company.replace(/\s+/g, '')}_cover_letter.pdf`}
                />
              )}
            </Box>
            <Box>
              <Heading as="h3" size="sm" mb={2}>
                Cover Letter Paragraphs
              </Heading>
              <CoverLetterParagraphDisplay
                paragraphs={comparison.cover_letter_paragraphs}
                onUpdate={handleCoverLetterParagraphUpdate}
              />
            </Box>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default ComparisonDetails;
