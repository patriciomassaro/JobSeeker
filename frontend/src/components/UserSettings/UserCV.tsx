import {
  Heading,
  Button,
  Container,
  Flex,
  Box,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import {
  type ApiError,
  type UserPublicMe,
  type UserUpdateMe,
  UsersService,
} from "../../client"
import useAuth from "../../hooks/useAuth"
import useCustomToast from "../../hooks/useCustomToast"
import ParseResume from "../UserSettings/ParseResume"
import { JsonDisplay } from "../Common/JsonDisplay"
import { PdfDisplay } from "../Common/PdfDisplay"
import { PdfUpload } from "../Common/PdfUpload"

const UserCV = () => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const { user: currentUser } = useAuth()
  const {
    handleSubmit,
    reset,
    getValues,
    formState: { isSubmitting, isDirty },
  } = useForm<UserPublicMe>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      resume: currentUser?.resume,
      parsed_work_experiences: currentUser?.parsed_work_experiences,
      parsed_educations: currentUser?.parsed_educations,
      parsed_languages: currentUser?.parsed_languages,
      parsed_skills: currentUser?.parsed_skills,
      additional_info: currentUser?.additional_info,

    },
  })

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const mutation = useMutation({
    mutationFn: (data: UserUpdateMe) =>
      UsersService.updateUserMe({ requestBody: data }),
    onSuccess: () => {
      showToast("Success!", "User updated successfully.", "success")
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
    },
  })

  const onSubmit: SubmitHandler<UserUpdateMe> = async (data) => {
    mutation.mutate(data)
  }

  const onCancel = () => {
    reset()
    toggleEditMode()
  }

  return (
    <>
      <Container maxW="full" as="form" onSubmit={handleSubmit(onSubmit)}>
        <Flex>

          <Box flex="1">
            <Heading as="h3" size="lg" mb={4}>Upload Your Resume</Heading>
            <PdfUpload />
          </Box>
          <Box flex="1">
            <Heading as="h3" size="lg" mb={4}></Heading>
            <ParseResume />
          </Box>
        </Flex>
        <PdfDisplay base64String={currentUser?.resume ?? null} />


        <JsonDisplay data={JSON.stringify(currentUser?.parsed_work_experiences)} title="Work Experiences" />
        <JsonDisplay data={JSON.stringify(currentUser?.parsed_educations)} title="Educations" />
        <JsonDisplay data={JSON.stringify(currentUser?.parsed_languages)} title="Languages" />
        <JsonDisplay data={JSON.stringify(currentUser?.parsed_skills)} title="Skills" />


        <Flex mt={4} gap={3}>
          <Button
            variant="primary"
            onClick={toggleEditMode}
            type={editMode ? "button" : "submit"}
            isLoading={editMode ? isSubmitting : false}
            isDisabled={editMode ? !isDirty || !getValues("username") : false}
          >
            {editMode ? "Save" : "Edit"}
          </Button>
          {editMode && (
            <Button onClick={onCancel} isDisabled={isSubmitting}>
              Cancel
            </Button>
          )}
        </Flex>
      </Container>
    </>
  )
}

export default UserCV 
