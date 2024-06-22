
import React from 'react';
import { Button, HStack, Text } from "@chakra-ui/react";

interface PaginationProps {
  currentPage: number;
  onPageChange: (pageNumber: number) => void;
  totalItems: number;
  itemsPerPage: number;
}

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  onPageChange,
  totalItems,
  itemsPerPage,
}) => {
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  return (
    <HStack spacing={4} justifyContent="center" my={4}>
      <Button onClick={handlePrevious} disabled={currentPage === 1}>
        Previous
      </Button>
      <Text>Page {currentPage} of {totalPages}</Text>
      <Button onClick={handleNext} disabled={currentPage === totalPages}>
        Next
      </Button>
    </HStack>
  );
};

export default Pagination;
