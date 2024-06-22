import React from "react";
import { Box, Text, IconButton, Flex } from "@chakra-ui/react";
import { EditIcon } from "@chakra-ui/icons";
import { CoverLetterParagraph as CoverLetterParagraphType } from "../../client/models";

interface CoverLetterParagraphProps {
  paragraph: CoverLetterParagraphType;
  onEdit: (paragraph: CoverLetterParagraphType) => void;
}

const CoverLetterParagraphDisplay: React.FC<CoverLetterParagraphProps> = ({ paragraph, onEdit }) => (
  <Box p={2} mb={2} border="1px solid #ccc" borderRadius="md" position="relative">
    <Flex justify="space-between" align="center">
      <Text fontWeight="bold">Paragraph {paragraph.paragraph_number}:</Text>
      <IconButton
        aria-label="Edit"
        icon={<EditIcon />}
        size="sm"
        onClick={() => onEdit(paragraph)}
        position="absolute"
        top="8px"
        right="8px"
      />
    </Flex>
    <Text>{paragraph.paragraph_text}</Text>
  </Box>
);

export default CoverLetterParagraphDisplay;
