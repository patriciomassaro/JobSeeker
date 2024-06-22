import React, { useState, useEffect } from 'react';
import { Button, FormControl, FormLabel, Select, Slider, SliderTrack, SliderFilledTrack, SliderThumb, useToast, Text, Box, Heading } from '@chakra-ui/react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { UsersService, ModelNamesService } from '../../client';


const ParseResume: React.FC = () => {
  const queryClient = useQueryClient();
  const [model, setModel] = useState<string>('GPT4_O');
  const [temperature, setTemperature] = useState<number>(0.5);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [modelOptions, setModelOptions] = useState<{ llm_alias: string, llm_value: string }[]>([]);

  const toast = useToast();

  useEffect(() => {
    const fetchModelNames = async () => {
      try {
        const response = await ModelNamesService.getModelNames();
        setModelOptions(response);
        if (response.length > 0) {
          console.log(response)
          setModel(response[0].llm_alias); // Set the first option as the default

        }
      } catch (error) {
        console.error("Error fetching model names:", error);
        toast({
          title: 'Error!',
          description: 'Failed to fetch model names.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    };

    fetchModelNames();
  }, [toast]);


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
      queryClient.invalidateQueries({ queryKey: ["users"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      setIsLoading(false);

    },

  });

  const handleParse = () => {
    mutation.mutate();
  }
  return (
    <FormControl>
      <Heading as="h3" size="md" mb={4}>Parse your resume using LLMs</Heading>
      <FormLabel>Select Model</FormLabel>
      <Select value={model} onChange={(e) => setModel(e.target.value)}>
        {modelOptions.map(option => (
          <option key={option.llm_value} value={option.llm_alias}>{option.llm_alias}</option>
        ))}
      </Select>
      <FormLabel mt={4}>Set Temperature</FormLabel>
      <Box display="flex" alignItems="center">
        <Slider
          defaultValue={0.5}
          min={0}
          max={2}
          step={0.01}
          value={temperature}
          onChange={(val) => setTemperature(val)}
          flex="1"
          mr={4}
        >
          <SliderTrack>
            <SliderFilledTrack />
          </SliderTrack>
          <SliderThumb />
        </Slider>
        <Text>{temperature.toFixed(2)}</Text>      </Box>
      <Box mt={4} display="flex" alignItems="center">
        <Button onClick={handleParse} isLoading={isLoading} isDisabled={isLoading} mr={4}>Parse Resume</Button>
      </Box>
    </FormControl >
  );
};

export default ParseResume;
