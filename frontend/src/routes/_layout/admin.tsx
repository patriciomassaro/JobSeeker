import {
  Badge,
  Box,
  Container,
  Flex,
  Heading,
  SkeletonText,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react"
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import { Suspense } from "react"
import { type UserPublicMe, UsersService } from "../../client"
// import ActionsMenu from "../../components/Common/ActionsMenu"

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
})

const MembersTableBody = () => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublicMe>(["currentUser"])

  const { data: user } = useSuspenseQuery({
    queryKey: ["user"],
    queryFn: () => UsersService.readUserMe(),
  })

  return (
    <Tbody>
      <Tr key={user.id}>
        <Td color={!user.name ? "ui.dim" : "inherit"}>
          {user.name || "N/A"}
          {currentUser?.id === user.id && (
            <Badge ml="1" colorScheme="teal">
              You
            </Badge>
          )}
        </Td>
        <Td>{user.username}</Td>
        <Td>{user.is_superuser ? "Superuser" : "User"}</Td>
        <Td>
          <Flex gap={2}>
            <Box
              w="2"
              h="2"
              borderRadius="50%"
              bg={user.is_superuser ? "ui.success" : "ui.danger"}
              alignSelf="center"
            />
            {user.is_superuser ? "Active" : "Inactive"}
          </Flex>
        </Td>
        <Td>
          {/* <ActionsMenu */}
          {/*   type="User" */}
          {/*   value={user} */}
          {/*   disabled={currentUser?.id === user.id ? true : false} */}
          {/* /> */}
        </Td>
      </Tr>
    </Tbody>
  )
}

const MembersBodySkeleton = () => {
  return (
    <Tbody>
      <Tr>
        {new Array(5).fill(null).map((_, index) => (
          <Td key={index}>
            <SkeletonText noOfLines={1} paddingBlock="16px" />
          </Td>
        ))}
      </Tr>
    </Tbody>
  )
}

function Admin() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        User Management
      </Heading>
      <TableContainer>
        <Table fontSize="md" size={{ base: "sm", md: "md" }}>
          <Thead>
            <Tr>
              <Th width="20%">Full name</Th>
              <Th width="50%">Email</Th>
              <Th width="10%">Role</Th>
              <Th width="10%">Status</Th>
              <Th width="10%">Actions</Th>
            </Tr>
          </Thead>
          <Suspense fallback={<MembersBodySkeleton />}>
            <MembersTableBody />
          </Suspense>
        </Table>
      </TableContainer>
    </Container>
  )
}
