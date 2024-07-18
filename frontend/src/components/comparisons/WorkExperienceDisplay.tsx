import React, { useState, useEffect } from "react";
import {
  Box,
  Text,
  IconButton,
  Flex,
  Input,
  Button,
  useToast,
  VStack,
  HStack,
} from "@chakra-ui/react";
import { EditIcon, CheckIcon, CloseIcon, AddIcon, DeleteIcon } from "@chakra-ui/icons";
import { WorkExperience } from "../../client/models";
import { UserComparisonServices } from "../../client/services";

interface WorkExperiencesProps {
  experiences: WorkExperience[] | undefined;
  onUpdate: () => void;
}

const WorkExperienceDisplay: React.FC<WorkExperiencesProps> = ({ experiences, onUpdate }) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editedExperiences, setEditedExperiences] = useState<WorkExperience[]>([]);
  const [newAccomplishment, setNewAccomplishment] = useState("");
  const toast = useToast();

  useEffect(() => {
    if (experiences) {
      setEditedExperiences(experiences);
    }
  }, [experiences]);

  const handleEdit = (index: number) => {
    setEditingIndex(index);
  };

  const handleSave = async (index: number) => {
    const experienceToSave = editedExperiences[index];

    if (!experienceToSave.title || !experienceToSave.company || !experienceToSave.start_year) {
      toast({
        title: "Error",
        description: "Title, company, and start year are required",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    const updatedExperience = {
      ...experienceToSave,
      start_year: Number(experienceToSave.start_year),
      start_month: experienceToSave.start_month ? Number(experienceToSave.start_month) : null,
      end_year: experienceToSave.end_year ? Number(experienceToSave.end_year) : null,
      end_month: experienceToSave.end_month ? Number(experienceToSave.end_month) : null,
    };

    try {
      await UserComparisonServices.editWorkExperience({
        newWorkExperience: updatedExperience
      });
      toast({
        title: "Work Experience updated",
        description: `Experience ${index + 1} has been successfully updated.`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      setEditingIndex(null);
      onUpdate();
    } catch (error) {
      console.error("Error updating work experience:", error);
      toast({
        title: "Error",
        description: "Failed to update work experience",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleCancel = (index: number) => {
    if (experiences) {
      setEditedExperiences(prevExperiences => {
        const newExperiences = [...prevExperiences];
        newExperiences[index] = experiences[index];
        return newExperiences;
      });
    }
    setEditingIndex(null);
  };

  const handleChange = (index: number, field: keyof WorkExperience, value: string | number) => {
    setEditedExperiences(prevExperiences => {
      const newExperiences = [...prevExperiences];
      if (field === 'start_year' || field === 'start_month' || field === 'end_year' || field === 'end_month') {
        newExperiences[index] = {
          ...newExperiences[index],
          [field]: value === "" ? null : Number(value)
        };
      } else {
        newExperiences[index] = { ...newExperiences[index], [field]: value };
      }
      return newExperiences;
    });
  };

  const handleAddAccomplishment = (index: number) => {
    if (newAccomplishment.trim()) {
      setEditedExperiences(prevExperiences => {
        const newExperiences = [...prevExperiences];
        newExperiences[index] = {
          ...newExperiences[index],
          accomplishments: [...(newExperiences[index].accomplishments || []), newAccomplishment.trim()]
        };
        return newExperiences;
      });
      setNewAccomplishment("");
    }
  };

  const handleEditAccomplishment = (experienceIndex: number, accomplishmentIndex: number, value: string) => {
    setEditedExperiences(prevExperiences => {
      const newExperiences = [...prevExperiences];
      const newAccomplishments = [...(newExperiences[experienceIndex].accomplishments || [])];
      newAccomplishments[accomplishmentIndex] = value;
      newExperiences[experienceIndex] = { ...newExperiences[experienceIndex], accomplishments: newAccomplishments };
      return newExperiences;
    });
  };

  const handleRemoveAccomplishment = (experienceIndex: number, accomplishmentIndex: number) => {
    setEditedExperiences(prevExperiences => {
      const newExperiences = [...prevExperiences];
      const newAccomplishments = (newExperiences[experienceIndex].accomplishments || []).filter((_, index) => index !== accomplishmentIndex);
      newExperiences[experienceIndex] = { ...newExperiences[experienceIndex], accomplishments: newAccomplishments };
      return newExperiences;
    });
  };

  if (!experiences || experiences.length === 0) {
    return <Box>No work experiences available.</Box>;
  }

  return (
    <VStack align="stretch" spacing={4}>
      {editedExperiences.map((experience, index) => (
        <Box key={experience.id} p={4} border="1px solid #ccc" borderRadius="md" position="relative">
          {editingIndex === index ? (
            <VStack spacing={3} align="stretch">
              <Input
                value={experience.title}
                onChange={(e) => handleChange(index, 'title', e.target.value)}
                placeholder="Title"
                isRequired
              />
              <Input
                value={experience.company}
                onChange={(e) => handleChange(index, 'company', e.target.value)}
                placeholder="Company"
                isRequired
              />
              <HStack>
                <Input
                  type="number"
                  value={experience.start_year ?? ""}
                  onChange={(e) => handleChange(index, 'start_year', e.target.value)}
                  placeholder="Start Year"
                  isRequired
                />
                <Input
                  type="number"
                  value={experience.start_month ?? ""}
                  onChange={(e) => handleChange(index, 'start_month', e.target.value)}
                  placeholder="Start Month"
                  min={1}
                  max={12}
                />
              </HStack>
              <HStack>
                <Input
                  type="number"
                  value={experience.end_year ?? ""}
                  onChange={(e) => handleChange(index, 'end_year', e.target.value)}
                  placeholder="End Year"
                />
                <Input
                  type="number"
                  value={experience.end_month ?? ""}
                  onChange={(e) => handleChange(index, 'end_month', e.target.value)}
                  placeholder="End Month"
                  min={1}
                  max={12}
                />
              </HStack>
              <Text fontWeight="bold">Accomplishments:</Text>
              {(experience.accomplishments || []).map((accomplishment, accIndex) => (
                <HStack key={accIndex}>
                  <Input
                    value={accomplishment}
                    onChange={(e) => handleEditAccomplishment(index, accIndex, e.target.value)}
                  />
                  <IconButton
                    aria-label="Remove accomplishment"
                    icon={<DeleteIcon />}
                    onClick={() => handleRemoveAccomplishment(index, accIndex)}
                  />
                </HStack>
              ))}
              <HStack>
                <Input
                  value={newAccomplishment}
                  onChange={(e) => setNewAccomplishment(e.target.value)}
                  placeholder="New accomplishment"
                />
                <Button onClick={() => handleAddAccomplishment(index)} leftIcon={<AddIcon />}>
                  Add
                </Button>
              </HStack>
              <Flex justify="flex-end" mt={4}>
                <Button onClick={() => handleSave(index)} colorScheme="green" mr={2}>
                  <CheckIcon mr={2} /> Save
                </Button>
                <Button onClick={() => handleCancel(index)} colorScheme="red">
                  <CloseIcon mr={2} /> Cancel
                </Button>
              </Flex>
            </VStack>
          ) : (
            <>
              <IconButton
                aria-label="Edit"
                icon={<EditIcon />}
                size="sm"
                onClick={() => handleEdit(index)}
                position="absolute"
                top={2}
                right={2}
              />
              <VStack align="stretch" spacing={2}>
                <Text fontWeight="bold">{experience.title}</Text>
                <Text>{experience.company}</Text>
                <Text>{`${experience.start_year}${experience.start_month ? `-${experience.start_month}` : ''} - ${experience.end_year ? `${experience.end_year}${experience.end_month ? `-${experience.end_month}` : ''}` : 'Present'}`}</Text>
                <Text fontWeight="bold" mt={2}>Accomplishments:</Text>
                <VStack align="stretch" pl={4}>
                  {(experience.accomplishments || []).map((accomplishment, accIndex) => (
                    <Text key={accIndex}>• {accomplishment}</Text>
                  ))}
                </VStack>
              </VStack>
            </>
          )}
        </Box>
      ))}
    </VStack>
  );
};

export default WorkExperienceDisplay;
