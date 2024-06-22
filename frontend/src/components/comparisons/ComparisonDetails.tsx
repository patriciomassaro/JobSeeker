import React, { useState } from "react";
import {
  Box, Heading, Text, Flex, Button
} from "@chakra-ui/react";
import { CoverLetterParagraph, UserJobPostingComparison, WorkExperience } from "../../client/models";
import { PdfDisplay } from "../Common/PdfDisplay";
import WorkExperienceDisplay from "./WorkExperienceDisplay";
import CoverLetterParagraphDisplay from "./CoverLetterParagraphDisplay";
import ModelTemperatureSelector from "../Common/ModelTemperatureSelector";  // Make sure to adjust the import path

interface JobComparisonDetailsProps {
  comparison: UserJobPostingComparison;
}

const JobComparisonDetails: React.FC<JobComparisonDetailsProps> = ({ comparison }) => {
  const [model, setModel] = useState<string>("");
  const [temperature, setTemperature] = useState<number>(0.5);

  const handleGeneratePDF = () => {
    // Logic to generate or regenerate the PDF with the selected model and temperature
    console.log(`Generating PDF with model: ${model} and temperature: ${temperature}`);
  };

  const handleEditExperience = (experience: WorkExperience) => {
    // Logic for editing the experience
    console.log('Editing experience:', experience);
  };

  const handleEditCoverLetterParagraph = (cover_letter_paragraph: CoverLetterParagraph) => {
    // Logic for editing the experience
    console.log('Editing cover letter paragraph:', cover_letter_paragraph);
  };

  return (
    <Box p={4} height="100%" overflow="hidden">
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

      <Flex height="calc(100% - 160px)" overflow="hidden">
        <Box width="50%" p={2} borderRight="1px solid #ccc" height="100%" overflowY="auto">
          <Heading as="h2" size="md" mb={2}>
            Resume
          </Heading>
          <Box mb={4}>
            {comparison.resume ? (
              <>
                <Button onClick={handleGeneratePDF} mb={4}>
                  Do you want to regenerate the PDF?
                </Button>
                <PdfDisplay base64String={comparison.resume} />
              </>
            ) : (
              <>
                <Text>No resume available</Text>
                <Button onClick={handleGeneratePDF} mb={4}>
                  Do you want to generate a PDF?
                </Button>
              </>
            )}
          </Box>
          <Box>
            <Heading as="h3" size="sm" mb={2}>
              Work Experiences
            </Heading>
            {comparison.work_experiences.map((experience, index) => (
              <WorkExperienceDisplay key={index} experience={experience} onEdit={handleEditExperience} />
            ))}
          </Box>
        </Box>

        <Box width="50%" p={2} height="100%" overflowY="auto">
          <Heading as="h2" size="md" mb={2}>
            Cover Letter
          </Heading>
          <Box mb={4}>
            {comparison.cover_letter ? (
              <>
                <Button onClick={handleGeneratePDF} mb={4}>
                  Do you want to regenerate the PDF?
                </Button>
                <PdfDisplay base64String={comparison.cover_letter} />
              </>
            ) : (
              <>
                <Text>No cover letter available</Text>
                <Button onClick={handleGeneratePDF} mb={4}>
                  Do you want to generate a PDF?
                </Button>
              </>
            )}
          </Box>
          <Box>
            <Heading as="h3" size="sm" mb={2}>
              Cover Letter Paragraphs
            </Heading>
            {comparison.cover_letter_paragraphs.map((paragraph, index) => (
              <CoverLetterParagraphDisplay key={index} paragraph={paragraph} onEdit={handleEditCoverLetterParagraph} />
            ))}
          </Box>
        </Box>
      </Flex>
    </Box>
  );
};

export default JobComparisonDetails;
