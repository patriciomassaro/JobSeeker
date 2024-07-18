import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type {
  Body_login_login_access_token, Message, NewPassword, Token, UserPublicMe, UpdatePassword, UserCreate, UserRegister, UserUpdateMe,
  ModelParameters, JobPostings, GetJobPostingParameters, UserJobPostingComparison, UserJobPostingComparisons, ModelNames, CoverLetterParagraph,
  WorkExperience
} from './models';

export type TDataLoginAccessToken = {
  formData: Body_login_login_access_token

}
export type TDataRecoverPassword = {
  email: string

}
export type TDataResetPassword = {
  requestBody: NewPassword

}
export type TDataRecoverPasswordHtmlContent = {
  email: string

}

export class LoginService {

  /**
   * Login Access Token
   * OAuth2 compatible token login, get an access token for future requests
   * @returns Token Successful Response
   * @throws ApiError
   */
  public static loginAccessToken(data: TDataLoginAccessToken): CancelablePromise<Token> {
    const {
      formData,
    } = data;
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/login/access-token',
      formData: formData,
      mediaType: 'application/x-www-form-urlencoded',
      errors: {
        422: `Validation Error`,
      },
    });
  }

  /**
   * Test Token
   * Test access token
   * @returns UserPublic Successful Response
   * @throws ApiError
   */
  public static testToken(): CancelablePromise<UserPublicMe> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/login/test-token',
    });
  }

  /**
   * Recover Password
   * Password Recovery
   * @returns Message Successful Response
   * @throws ApiError
   */
  public static recoverPassword(data: TDataRecoverPassword): CancelablePromise<Message> {
    const {
      email,
    } = data;
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/password-recovery/{email}',
      path: {
        email
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }

  /**
   * Reset Password
   * Reset password
   * @returns Message Successful Response
   * @throws ApiError
   */
  public static resetPassword(data: TDataResetPassword): CancelablePromise<Message> {
    const {
      requestBody,
    } = data;
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/reset-password/',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }

  /**
   * Recover Password Html Content
   * HTML Content for Password Recovery
   * @returns string Successful Response
   * @throws ApiError
   */
  public static recoverPasswordHtmlContent(data: TDataRecoverPasswordHtmlContent): CancelablePromise<string> {
    const {
      email,
    } = data;
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/password-recovery-html-content/{email}',
      path: {
        email
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }

}

export type TDataReadUsers = {
  limit?: number
  skip?: number

}
export type TDataCreateUser = {
  requestBody: UserCreate

}
export type TDataUpdateUserMe = {
  requestBody: UserUpdateMe

}
export type TDataUpdatePasswordMe = {
  requestBody: UpdatePassword

}
export type TDataUserUploadCV = {
  requestBody: FormData
}
export type TDataRegisterUser = {
  requestBody: UserRegister

}
export type TDataReadUserById = {
  userId: number

}
export type TDataDeleteUser = {
  userId: number

}

export type TDataparseResume = {
  requestBody: ModelParameters
}

export type TDataUserUploadResume = {
  formData: FormData;
};

export class UsersService {
  /**
   * Create User
   * Create new user.
   * @returns UserPublic Successful Response
   * @throws ApiError
   */
  public static createUser(data: TDataCreateUser): CancelablePromise<UserPublicMe> {
    const {
      requestBody,
    } = data;
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/users/',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }

  /**
   * Read User Me
   * Get current user.
   * @returns UserPublic Successful Response
   * @throws ApiError
   */
  public static readUserMe(): CancelablePromise<UserPublicMe> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/users/me',
    });
  }

  /**
   * Update User Me
   * Update own user.
   * @returns UserPublic Successful Response
   * @throws ApiError
   */
  public static updateUserMe(data: TDataUpdateUserMe): CancelablePromise<UserPublicMe> {
    const {
      requestBody,
    } = data;
    return __request(OpenAPI, {
      method: 'PATCH',
      url: '/api/v1/users/me',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }

  /**
   * Update Password Me
   * Update own password.
   * @returns Message Successful Response
   * @throws ApiError
   */
  public static updatePasswordMe(data: TDataUpdatePasswordMe): CancelablePromise<Message> {
    const {
      requestBody,
    } = data;
    return __request(OpenAPI, {
      method: 'PATCH',
      url: '/api/v1/users/me/password',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }

  /**
   * Register User
   * Create new user without the need to be logged in.
   * @returns UserPublic Successful Response
   * @throws ApiError
   */
  public static registerUser(data: TDataRegisterUser): CancelablePromise<UserPublicMe> {
    const {
      requestBody,
    } = data;
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/users/signup',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }


  /**
  * Upload CV of the current user
  * @returns Message Successful Response
  * @throws ApiError
  */
  public static uploadResume(data: TDataUserUploadResume): CancelablePromise<Message> {
    const { formData } = data;
    return __request(OpenAPI, {
      method: 'PATCH',
      url: '/api/v1/users/me/upload-resume',
      body: formData,
      mediaType: 'multipart/form-data',
      errors: {
        422: `Validation Error`,
      },

    },);
  }
  /** 
   * Parse CV of the current user
  * @returns Message Successful Response
  * @throws ApiError
  */
  public static parseResume(data: TDataparseResume): CancelablePromise<Message> {
    const { requestBody } = data;
    return __request(OpenAPI, {
      body: requestBody,
      method: 'PATCH',
      url: '/api/v1/users/me/parse-resume',
    });
  }


  /**
   * Delete User
   * Delete a user.
   * @returns Message Successful Response
   * @throws ApiError
   */
  public static deleteUser(data: TDataDeleteUser): CancelablePromise<Message> {
    const {
      userId,
    } = data;
    return __request(OpenAPI, {
      method: 'DELETE',
      url: '/api/v1/users/{user_id}',
      path: {
        user_id: userId
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }


}

export type TDataTestEmail = {
  emailTo: string

}

export class UtilsService {

  /**
   * Test Email
   * Test emails.
   * @returns Message Successful Response
   * @throws ApiError
   */
  public static testEmail(data: TDataTestEmail): CancelablePromise<Message> {
    const {
      emailTo,
    } = data;
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/utils/test-email/',
      query: {
        email_to: emailTo
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }

}

export type TDataGetJobPostings = {
  requestBody: GetJobPostingParameters
}

export class JobPostingServices {

  /**
   * Get job posting items.
   * @returns JobPostings Successful Response
   * @throws ApiError
   */
  public static getJobPostings(data: TDataGetJobPostings): CancelablePromise<JobPostings> {
    const { requestBody } = data;
    const queryParams = new URLSearchParams(requestBody as any).toString();
    return __request(OpenAPI, {
      method: 'GET',
      url: `/api/v1/job-postings?${queryParams}`,
      errors: {
        422: `Validation Error`,
      },
    });
  }
}


export class UserComparisonServices {
  /**
   * Get comparison status for a job posting.
   * @param job_posting_id - The ID of the job posting.
   * @param comparison_id - The ID of the comparison.
   * @returns Message - The comparison status message.
   * @throws ApiError
   */
  public static getUserComparison(data: { comparison_id: number | null, job_posting_id: number | null }): CancelablePromise<UserJobPostingComparison> {
    const queryParams = new URLSearchParams();

    if (data.comparison_id !== null) {
      queryParams.append("comparison_id", data.comparison_id.toString());
    }

    if (data.job_posting_id !== null) {
      queryParams.append("job_posting_id", data.job_posting_id.toString());
    }
    return __request(OpenAPI, {
      method: 'GET',
      url: `/api/v1/comparisons/?${queryParams}`,
      errors: {
        404: `Comparison not found`,
      },
    });
  }

  public static getUserComparisons(): CancelablePromise<UserJobPostingComparisons> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `/api/v1/comparisons/current_user`,
      errors: {
        404: `Current user comparisos not found`,
      },
    });
  }

  public static generateWorkExperiences(data: { comparison_id: number }, parameters: ModelParameters): CancelablePromise<Message> {
    return __request(OpenAPI, {
      method: 'POST',
      url: `/api/v1/comparisons/generate-work-experiences?comparison_id=${data.comparison_id}`,
      body: parameters,
      errors: {
        500: `Server Error`,
      },
    });
  }

  public static generateCoverLetterParagraphs(data: { comparison_id: number }, parameters: ModelParameters): CancelablePromise<Message> {
    return __request(OpenAPI, {
      method: 'POST',
      url: `/api/v1/comparisons/generate-cover-letter-paragraphs?comparison_id=${data.comparison_id}`,
      body: parameters,
      errors: {
        500: `Server Error`,
      },
    });
  }


  /**
  * Activate comparison for a job posting.
  * @param job_posting_id - The ID of the job posting.
  * @returns Message - The activation status message.
  * @throws ApiError
  */
  public static activateUserComparison(data: { job_posting_id: number }): CancelablePromise<Message> {
    return __request(OpenAPI, {
      method: 'PATCH',
      url: `/api/v1/comparisons/create-activate?job_posting_id=${data.job_posting_id}`,
      errors: {
        500: `Server Error`,
      },
    });
  }
  public static editWorkExperience(data: { newWorkExperience: WorkExperience }): CancelablePromise<Message> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/comparisons/edit-work-experience',
      body: data.newWorkExperience,
      errors: {
        404: `User or Work Experience not found`,
        500: `Server Error`,
        400: `Bad Request`
      },
    });
  }

  public static editCoverLetterParagraph(data: { newCoverLetterParagraph: CoverLetterParagraph }): CancelablePromise<Message> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/comparisons/edit-cover-letter-paragraph',
      body: data.newCoverLetterParagraph,
      errors: {
        404: `User or Cover Letter Paragraph not found`,
        500: `Server Error`,
      },
    });
  }
  public static buildResume(data: { comparison_id: number }): CancelablePromise<Message> {
    return __request(OpenAPI, {
      method: 'PATCH',
      url: `/api/v1/comparisons/build-resume?comparison_id=${data.comparison_id}`,
      errors: {
        500: `Server Error`,
      },
    });
  }

  public static buildCoverLetter(data: { comparison_id: number }): CancelablePromise<Message> {
    return __request(OpenAPI, {
      method: 'PATCH',
      url: `/api/v1/comparisons/build-cover-letter?comparison_id=${data.comparison_id}`,
      errors: {
        500: `Server Error`,
      },
    });
  }
}




export class ModelNamesService {
  public static getModelNames(): CancelablePromise<ModelNames[]> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/model-names'
    })
  }
}

