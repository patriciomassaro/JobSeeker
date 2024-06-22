import React from "react";
import { List, ListItem, Text } from "@chakra-ui/react";
import { UserJobPostingComparison, UserJobPostingComparisons } from "../../client/models";

interface ComparisonListProps {
  jobComparisons: UserJobPostingComparisons;
  onComparisonSelect: (comparison: UserJobPostingComparison) => void;
}

const ComparisonList: React.FC<ComparisonListProps> = ({ jobComparisons, onComparisonSelect }) => {
  return (
    <List spacing={3}>
      {jobComparisons.data.map((comparison: UserJobPostingComparison) => (
        <ListItem
          key={comparison.id} // Ensure the key is unique for each item
          onClick={() => onComparisonSelect(comparison)}
          cursor="pointer"
          p={2}
          _hover={{ bg: "gray.100" }}
        >
          <Text fontWeight="bold">{comparison.title}</Text>
          <Text>{comparison.company}</Text>
          <Text>{comparison.location ?? "Unknown Location"}</Text>
        </ListItem>
      ))}
    </List>
  );
};

export default ComparisonList;
