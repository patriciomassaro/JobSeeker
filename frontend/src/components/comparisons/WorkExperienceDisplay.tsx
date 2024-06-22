import React from "react";
import { Box, Text, IconButton, Flex } from "@chakra-ui/react";
import { EditIcon } from "@chakra-ui/icons";
import { WorkExperience as WorkExperienceType } from "../../client/models";

interface WorkExperienceProps {
  experience: WorkExperienceType;
  onEdit: (experience: WorkExperienceType) => void;
}

const WorkExperienceDisplay: React.FC<WorkExperienceProps> = ({ experience,
  //  onEdit 
}) => (
  <Box p={2} mb={2} border="1px solid #ccc" borderRadius="md" position="relative">
    <Flex justify="space-between" align="center">
      <Text fontWeight="bold">Title:</Text>
      <IconButton
        aria-label="Edit"
        icon={<EditIcon />}
        size="sm"
        onClick={() => onEdit(experience)}
        position="absolute"
        top="8px"
        right="8px"
      />
    </Flex>
    <Text>{experience.title}</Text>
    <Text fontWeight="bold">Company:</Text>
    <Text>{experience.company}</Text>
    <Text fontWeight="bold">Start Date:</Text>
    <Text>{experience.start_date}</Text>
    <Text fontWeight="bold">End Date:</Text>
    <Text>{experience.end_date}</Text>
    <Text fontWeight="bold">Accomplishments:</Text>
    <ul>
      {experience.accomplishments.map((accomplishment, i) => (
        <li key={i}>{accomplishment}</li>
      ))}
    </ul>
  </Box>
);

export default WorkExperienceDisplay;
