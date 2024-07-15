import React, { useState } from 'react';
import { Button, FormControl, useToast, Box, Heading } from '@chakra-ui/react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { UsersService } from '../../client';
import ModelTemperatureSelector from '../Common/ModelTemperatureSelector';

const ParseResume: React.FC = () => {
  const queryClient = useQueryClient();
  const [model, setModel] = useState<string>('');
  const [temperature, setTemperature] = useState<number>(0.5);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const toast = useToast();

  const mutation = useMutation({
    mutationFn: () => UsersService.parseResume({
      requestBody: {
        name: model,
        temperature: temperature,
      },
    }),
    onMutate: () => {
      setIsLoading(true);
    },
    onSuccess: () => {
      toast({
        title: 'Success!',
        description: 'Resume parsed successfully.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    },
    onError: () => {
      toast({
        title: 'Error!',
        description: 'Failed to parse resume.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      setIsLoading(false);
    },
  });

  const handleParse = () => {
    mutation.mutate();
  }

  return (
    <FormControl>
      <Heading as="h3" size="md" mb={4}>Parse your resume using LLMs</Heading>
      <ModelTemperatureSelector
        model={model}
        setModel={setModel}
        temperature={temperature}
        setTemperature={setTemperature}
      />
      <Box mt={4} display="flex" alignItems="center">
        <Button onClick={handleParse} isLoading={isLoading} isDisabled={isLoading} mr={4}>
          Parse Resume
        </Button>
      </Box>
    </FormControl>
  );
};

export default ParseResume;
