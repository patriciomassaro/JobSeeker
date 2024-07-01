import React, { useState, useEffect } from "react";
import {
  Box,
  Text,
  IconButton,
  Flex,
  Textarea,
  Button,
  useToast,
  VStack,
} from "@chakra-ui/react";
import { EditIcon, CheckIcon, CloseIcon } from "@chakra-ui/icons";
import { CoverLetterParagraphPublic } from "../../client/models";
import { UserComparisonServices } from "../../client/services";

interface CoverLetterParagraphsProps {
  paragraphs: CoverLetterParagraphPublic[] | undefined;
  onUpdate: () => void;
}

const CoverLetterParagraph: React.FC<CoverLetterParagraphsProps> = ({ paragraphs, onUpdate }) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editedParagraphs, setEditedParagraphs] = useState<CoverLetterParagraphPublic[]>([]);
  const toast = useToast();

  useEffect(() => {
    if (paragraphs) {
      setEditedParagraphs(paragraphs);
    }
  }, [paragraphs]);

  const handleEdit = (index: number) => {
    setEditingIndex(index);
  };

  const handleSave = async (index: number) => {
    try {
      await UserComparisonServices.editCoverLetterParagraph({
        newCoverLetterParagraph: editedParagraphs[index]
      });
      toast({
        title: "Cover Letter Paragraph updated",
        description: `Paragraph ${index + 1} has been successfully updated.`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      setEditingIndex(null);
      onUpdate();
    } catch (error) {
      console.error("Error updating cover letter paragraph:", error);
      toast({
        title: "Error",
        description: "Failed to update cover letter paragraph",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleCancel = (index: number) => {
    if (paragraphs) {
      setEditedParagraphs(prevParagraphs => {
        const newParagraphs = [...prevParagraphs];
        newParagraphs[index] = paragraphs[index];
        return newParagraphs;
      });
    }
    setEditingIndex(null);
  };

  const handleChange = (index: number, newText: string) => {
    setEditedParagraphs(prevParagraphs => {
      const newParagraphs = [...prevParagraphs];
      newParagraphs[index] = { ...newParagraphs[index], paragraph_text: newText };
      return newParagraphs;
    });
  };

  if (!paragraphs || paragraphs.length === 0) {
    return <Box>No cover letter paragraphs available.</Box>;
  }

  return (
    <VStack align="stretch" spacing={4}>
      {editedParagraphs.map((paragraph, index) => (
        <Box key={paragraph.id} p={4} border="1px solid #ccc" borderRadius="md" position="relative">
          {editingIndex === index ? (
            <>
              <Textarea
                value={paragraph.paragraph_text}
                onChange={(e) => handleChange(index, e.target.value)}
                rows={4}
                mb={3}
              />
              <Flex justify="flex-end">
                <Button onClick={() => handleSave(index)} colorScheme="green" mr={2}>
                  <CheckIcon mr={2} /> Save
                </Button>
                <Button onClick={() => handleCancel(index)} colorScheme="red">
                  <CloseIcon mr={2} /> Cancel
                </Button>
              </Flex>
            </>
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
              <Text fontWeight="bold" mb={2}>Paragraph {paragraph.paragraph_number}</Text>
              <Text>{paragraph.paragraph_text}</Text>
            </>
          )}
        </Box>
      ))}
    </VStack>
  );
};

export default CoverLetterParagraph;
