import { Box, Code, Heading, useColorModeValue } from '@chakra-ui/react';

type JsonDisplayProps = {
  data: string;
  title?: string;
};

export const JsonDisplay = ({ data, title }: JsonDisplayProps) => {
  // Define colors that adapt to light or dark mode
  const boxBgColor = useColorModeValue('gray.100', 'gray.700');
  const textColor = useColorModeValue('black', 'white');

  return (
    <>
      {title && (
        <Heading size="sm" py={4}>
          {title}
        </Heading>
      )}
      <Box
        p={4}
        bg={boxBgColor} // Dynamically set background color
        color={textColor} // Dynamically set text color
        borderRadius="md"
        overflowX="auto"
      >
        <Code p={2} w="full" display="block" whiteSpace="pre-wrap">
          {JSON.stringify(JSON.parse(data), null, 2)}
        </Code>
      </Box>
    </>
  );
};
