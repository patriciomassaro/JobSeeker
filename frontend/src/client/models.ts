export type Body_login_login_access_token = {
  grant_type?: string | null;
  username: string;
  password: string;
  scope?: string;
  client_id?: string | null;
  client_secret?: string | null;
};



export type HTTPValidationError = {
  detail?: Array<ValidationError>;
};


export type Message = {
  message: string;
};



export type NewPassword = {
  token: string;
  new_password: string;
};



export type Token = {
  access_token: string;
  token_type?: string;
};



export type UpdatePassword = {
  current_password: string;
  new_password: string;
};



export type UserCreate = {
  email: string;
  is_active?: boolean;
  is_superuser?: boolean;
  full_name?: string | null;
  password: string;
};



export type UserPublicMe = {
  username: string
  name: string;
  id: number;
  date_created: Date;
  date_updated: Date;
  parsed_personal?: Record<string, any>; // `dict` in Python corresponds to an object in TypeScript
  parsed_work_experiences?: Record<string, any>;
  parsed_educations?: Record<string, any>;
  parsed_languages?: Record<string, any>;
  parsed_skills?: string[]; // List in Python translates directly to array in TypeScript
  additional_info?: string;
  resume?: string;
  is_superuser: boolean;
};


export type UserRegister = {
  email: string;
  password: string;
  full_name?: string | null;
};


export type UserUpdate = {
  email?: string | null;
  is_active?: boolean;
  is_superuser?: boolean;
  full_name?: string | null;
  password?: string | null;
};


export type UserUploadResume = {
  resume: File;
};

export type UserUpdateMe = {
  username?: string | null;
  name?: string | null;
  parsed_personal?: Record<string, any>;
  parsed_work_experiences?: Record<string, any>;
  parsed_educations?: Record<string, any>;
  parsed_languages?: Record<string, any>;
  parsed_skills?: string[];
  additional_info?: string;
};


export type ValidationError = {
  loc: Array<string | number>;
  msg: string;
  type: string;
};

export type ModelNames = {
  public_name: string;
}


export type ModelParameters = {
  name: string;
  temperature: number;
}

export type GetJobPostingParameters = {
  skip?: number;
  limit?: number;
  job_title?: string;
  company_name?: string;
};

export type JobPosting = {
  id: number;
  title: string;
  company: string;
  location: string | null;
  description: string;
  seniority_level: string | null;
  employment_type: string | null;
  experience_level: string | null;
  remote_modality: string | null;
  salary_range: string | null;
  industries: string[] | null;
  job_functions: string[] | null;
  skills: string[] | null;
  job_salary_min: number | null;
  job_salary_max: number | null;
  job_poster_name: string | null;
  job_poster_profile: string | null;
  summary: Record<string, any> | null;
  institution_about: string | null;
  institution_website: string | null;
  institution_industry: string | null;
  institution_size: string | null;
  institution_followers: number | null;
  institution_employees: number | null;
  institution_tagline: string | null;
  institution_location: string | null;
  institution_specialties: string[] | null;
};

export type JobPostings = {
  data: JobPosting[];
};

export type WorkExperience = {
  id: number;
  comparison_id: number;
  start_date: string;
  end_date: string;
  title: string;
  company: string;
  accomplishments: string[];
};

export type CoverLetterParagraph = {
  id: number;
  comparison_id: number;
  paragraph_number: number;
  paragraph_text: string;
};


export type UserJobPostingComparison = {
  id: number;
  user_id: number;
  job_posting_id: number;
  title: string;
  location: string | null;
  company: string;
  comparison: Record<string, any> | null;
  resume: string | null;
  cover_letter: string | null;
  is_active: boolean;
  work_experiences: WorkExperience[];
  cover_letter_paragraphs: CoverLetterParagraph[];
};
export interface UserJobPostingComparisons {
  data: UserJobPostingComparison[];
}


