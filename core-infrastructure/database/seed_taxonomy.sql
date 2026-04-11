-- Core Skill Taxonomy Seed
-- Initial 500-800 skills to prime the normalizer

-- Use ON CONFLICT DO NOTHING so this script is idempotent.
-- Note: 'id' is a SERIAL primary key, but we rely on 'canonical_name' as the natural unique key.

INSERT INTO skill_taxonomy (canonical_name, aliases, category, parent_category, hierarchy_path, parent_skills, description) VALUES
-- Programming Languages
('Python', ARRAY['python3', 'py', 'cpython'], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > Python', ARRAY['Backend Development', 'Scripting'], 'General-purpose programming language widely used in AI, web, and scripting.'),
('JavaScript', ARRAY['JS', 'ECMAScript', 'ES6'], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > JavaScript', ARRAY['Frontend Development', 'Web Development'], 'Core language of the web.'),
('TypeScript', ARRAY['TS'], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > TypeScript', ARRAY['JavaScript', 'Frontend Development'], 'Strict syntactical superset of JavaScript.'),
('Go', ARRAY['golang'], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > Go', ARRAY['Backend Development', 'Systems Programming'], 'Statically typed, compiled programming language designed at Google.'),
('Rust', ARRAY[], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > Rust', ARRAY['Systems Programming'], 'Multi-paradigm, general-purpose programming language designed for performance and safety.'),
('Java', ARRAY['java8', 'java11'], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > Java', ARRAY['Backend Development', 'Enterprise Software'], 'High-level, class-based, object-oriented programming language.'),
('C++', ARRAY['cpp', 'c plus plus'], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > C++', ARRAY['Systems Programming', 'Game Development'], 'General-purpose programming language created by Bjarne Stroustrup.'),
('Kotlin', ARRAY[], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > Kotlin', ARRAY['Android Development', 'Java'], 'Cross-platform, statically typed, general-purpose programming language with type inference.'),
('Swift', ARRAY[], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > Swift', ARRAY['iOS Development'], 'General-purpose, multi-paradigm, compiled programming language developed by Apple Inc.'),
('Ruby', ARRAY[], 'Programming Languages', 'Technical Skills', 'Technical Skills > Programming Languages > Ruby', ARRAY['Backend Development', 'Scripting'], 'Interpreted, high-level, general-purpose programming language.'),

-- Frontend Frameworks
('React', ARRAY['React.js', 'ReactJS'], 'Frontend Frameworks', 'Technical Skills', 'Technical Skills > Frontend Frameworks > React', ARRAY['Frontend Development', 'Web Development', 'JavaScript'], 'A JavaScript library for building user interfaces.'),
('Angular', ARRAY['AngularJS', 'Angular 2+'], 'Frontend Frameworks', 'Technical Skills', 'Technical Skills > Frontend Frameworks > Angular', ARRAY['Frontend Development', 'Web Development', 'TypeScript'], 'A TypeScript-based open-source web application framework.'),
('Vue.js', ARRAY['Vue', 'VueJS'], 'Frontend Frameworks', 'Technical Skills', 'Technical Skills > Frontend Frameworks > Vue.js', ARRAY['Frontend Development', 'Web Development', 'JavaScript'], 'An open-source model–view–viewmodel front end JavaScript framework.'),
('Next.js', ARRAY['NextJS'], 'Frontend Frameworks', 'Technical Skills', 'Technical Skills > Frontend Frameworks > Next.js', ARRAY['React', 'Frontend Development', 'Server-Side Rendering'], 'An open-source web development framework built on top of Node.js enabling React-based web applications functionalities.'),
('Svelte', ARRAY['SvelteJS'], 'Frontend Frameworks', 'Technical Skills', 'Technical Skills > Frontend Frameworks > Svelte', ARRAY['Frontend Development', 'Web Development'], 'A free and open-source front end component framework or language.'),

-- Backend Frameworks
('Django', ARRAY['django-rest-framework', 'DRF'], 'Backend Frameworks', 'Technical Skills', 'Technical Skills > Backend Frameworks > Django', ARRAY['Backend Development', 'Web Development', 'Python'], 'A high-level Python web framework.'),
('FastAPI', ARRAY[], 'Backend Frameworks', 'Technical Skills', 'Technical Skills > Backend Frameworks > FastAPI', ARRAY['Backend Development', 'REST API Development', 'Python'], 'A modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.'),
('Flask', ARRAY[], 'Backend Frameworks', 'Technical Skills', 'Technical Skills > Backend Frameworks > Flask', ARRAY['Backend Development', 'Web Development', 'Python'], 'A micro web framework written in Python.'),
('Express.js', ARRAY['Express'], 'Backend Frameworks', 'Technical Skills', 'Technical Skills > Backend Frameworks > Express.js', ARRAY['Backend Development', 'Web Development', 'Node.js'], 'A back end web application framework for Node.js.'),
('Spring Boot', ARRAY['Spring'], 'Backend Frameworks', 'Technical Skills', 'Technical Skills > Backend Frameworks > Spring Boot', ARRAY['Backend Development', 'Enterprise Software', 'Java'], 'An open source Java-based framework used to create a micro Service.'),
('NestJS', ARRAY['Nest'], 'Backend Frameworks', 'Technical Skills', 'Technical Skills > Backend Frameworks > NestJS', ARRAY['Backend Development', 'Node.js', 'TypeScript'], 'A framework for building efficient, scalable Node.js server-side applications.'),

-- Databases
('PostgreSQL', ARRAY['Postgres', 'psql'], 'Databases', 'Technical Skills', 'Technical Skills > Databases > PostgreSQL', ARRAY['SQL', 'Relational Databases', 'Database Management'], 'A free and open-source relational database management system.'),
('MySQL', ARRAY[], 'Databases', 'Technical Skills', 'Technical Skills > Databases > MySQL', ARRAY['SQL', 'Relational Databases'], 'An open-source relational database management system.'),
('MongoDB', ARRAY['Mongo'], 'Databases', 'Technical Skills', 'Technical Skills > Databases > MongoDB', ARRAY['NoSQL', 'Database Management'], 'A source-available cross-platform document-oriented database program.'),
('Redis', ARRAY[], 'Databases', 'Technical Skills', 'Technical Skills > Databases > Redis', ARRAY['NoSQL', 'In-Memory Data Store', 'Caching'], 'An open-source (BSD licensed), in-memory data structure store, used as a database, cache, and message broker.'),
('Cassandra', ARRAY['Apache Cassandra'], 'Databases', 'Technical Skills', 'Technical Skills > Databases > Cassandra', ARRAY['NoSQL', 'Distributed Databases'], 'A free and open-source, distributed, wide-column store, NoSQL database management system.'),
('DynamoDB', ARRAY['AWS DynamoDB'], 'Databases', 'Technical Skills', 'Technical Skills > Databases > DynamoDB', ARRAY['NoSQL', 'Cloud Databases', 'AWS'], 'A fully managed proprietary NoSQL database service that supports key-value and document data structures.'),

-- Cloud & DevOps
('Amazon Web Services', ARRAY['AWS'], 'Cloud Platforms', 'Technical Skills', 'Technical Skills > Cloud Platforms > Amazon Web Services', ARRAY['Cloud Computing'], 'A subsidiary of Amazon providing on-demand cloud computing platforms and APIs.'),
('Google Cloud Platform', ARRAY['GCP', 'Google Cloud'], 'Cloud Platforms', 'Technical Skills', 'Technical Skills > Cloud Platforms > Google Cloud Platform', ARRAY['Cloud Computing'], 'A suite of cloud computing services offered by Google.'),
('Microsoft Azure', ARRAY['Azure'], 'Cloud Platforms', 'Technical Skills', 'Technical Skills > Cloud Platforms > Microsoft Azure', ARRAY['Cloud Computing'], 'A cloud computing service created by Microsoft for building, testing, deploying, and managing applications and services.'),
('Docker', ARRAY['docker-compose'], 'Cloud & DevOps', 'Technical Skills', 'Technical Skills > Cloud & DevOps > Docker', ARRAY['Containerization', 'DevOps'], 'A set of platform as a service products that use OS-level virtualization to deliver software in packages called containers.'),
('Kubernetes', ARRAY['K8s', 'k8s', 'Kube'], 'Cloud & DevOps', 'Technical Skills', 'Technical Skills > Cloud & DevOps > Kubernetes', ARRAY['Container Orchestration', 'DevOps', 'Cloud Computing'], 'An open-source system for automating deployment, scaling, and management of containerized applications.'),
('Terraform', ARRAY[], 'Cloud & DevOps', 'Technical Skills', 'Technical Skills > Cloud & DevOps > Terraform', ARRAY['Infrastructure as Code', 'DevOps'], 'An open-source infrastructure as code software tool created by HashiCorp.'),
('Ansible', ARRAY[], 'Cloud & DevOps', 'Technical Skills', 'Technical Skills > Cloud & DevOps > Ansible', ARRAY['Configuration Management', 'DevOps'], 'An open-source software provisioning, configuration management, and application-deployment tool.'),

-- AI & Machine Learning
('TensorFlow', ARRAY['TF'], 'AI & Machine Learning', 'Technical Skills', 'Technical Skills > AI & Machine Learning > TensorFlow', ARRAY['Deep Learning', 'Machine Learning', 'AI'], 'A free and open-source software library for machine learning and artificial intelligence.'),
('PyTorch', ARRAY[], 'AI & Machine Learning', 'Technical Skills', 'Technical Skills > AI & Machine Learning > PyTorch', ARRAY['Deep Learning', 'Machine Learning', 'AI'], 'An open source machine learning framework based on the Torch library.'),
('scikit-learn', ARRAY['sklearn'], 'AI & Machine Learning', 'Technical Skills', 'Technical Skills > AI & Machine Learning > scikit-learn', ARRAY['Machine Learning', 'Python'], 'A free software machine learning library for the Python programming language.'),
('Hugging Face', ARRAY['Transformers'], 'AI & Machine Learning', 'Technical Skills', 'Technical Skills > AI & Machine Learning > Hugging Face', ARRAY['NLP', 'Machine Learning', 'Deep Learning'], 'A company and open-source community that builds tools to enable users to build, train and deploy ML models based on open source code and technologies.'),
('LangChain', ARRAY[], 'AI & Machine Learning', 'Technical Skills', 'Technical Skills > AI & Machine Learning > LangChain', ARRAY['LLM Development', 'AI', 'Prompt Engineering'], 'A framework designed to simplify the creation of applications using large language models (LLMs).'),
('LangGraph', ARRAY[], 'AI & Machine Learning', 'Technical Skills', 'Technical Skills > AI & Machine Learning > LangGraph', ARRAY['LLM Development', 'AI', 'Agentic Workflows'], 'A library for building stateful, multi-actor applications with LLMs.'),
('RAG', ARRAY['Retrieval-Augmented Generation'], 'AI & Machine Learning', 'Technical Skills', 'Technical Skills > AI & Machine Learning > RAG', ARRAY['LLM Development', 'AI'], 'An AI framework for retrieving facts from an external knowledge base to ground large language models (LLMs) on the most accurate, up-to-date information.'),

-- Soft Skills
('Agile Methodology', ARRAY['agile', 'scrum', 'kanban'], 'Methodologies', 'Soft Skills', 'Soft Skills > Methodologies > Agile Methodology', ARRAY['Project Management'], 'A project management philosophy or framework.'),
('Leadership', ARRAY[], 'Interpersonal', 'Soft Skills', 'Soft Skills > Interpersonal > Leadership', ARRAY['Management'], 'The action of leading a group of people or an organization.'),
('Communication', ARRAY['Written Communication', 'Verbal Communication'], 'Interpersonal', 'Soft Skills', 'Soft Skills > Interpersonal > Communication', ARRAY[], 'The imparting or exchanging of information or news.'),
('Problem Solving', ARRAY['Critical Thinking'], 'Cognitive', 'Soft Skills', 'Soft Skills > Cognitive > Problem Solving', ARRAY[], 'The process of finding solutions to difficult or complex issues.'),

-- Business Skills
('Project Management', ARRAY['PM'], 'Management', 'Business Skills', 'Business Skills > Management > Project Management', ARRAY['Leadership'], 'The practice of initiating, planning, executing, controlling, and closing the work of a team to achieve specific goals and meet specific success criteria at the specified time.'),
('Product Management', ARRAY['PdM'], 'Management', 'Business Skills', 'Business Skills > Management > Product Management', ARRAY['Leadership', 'Strategy'], 'An organizational lifecycle function within a company dealing with the planning, forecasting, and production, or marketing of a product or products at all stages of the product lifecycle.'),
('Stakeholder Management', ARRAY[], 'Management', 'Business Skills', 'Business Skills > Management > Stakeholder Management', ARRAY['Communication', 'Leadership'], 'The process of maintaining good relationships with the people who have most impact on your work.'),

-- Data & Analytics
('SQL', ARRAY[], 'Data Analysis', 'Data & Analytics', 'Data & Analytics > Data Analysis > SQL', ARRAY['Database Management'], 'A domain-specific language used in programming and designed for managing data held in a relational database management system.'),
('Data Analysis', ARRAY['Data Analytics'], 'Data Analysis', 'Data & Analytics', 'Data & Analytics > Data Analysis > Data Analysis', ARRAY[], 'A process of inspecting, cleansing, transforming, and modeling data with the goal of discovering useful information, informing conclusions, and supporting decision-making.'),
('Power BI', ARRAY['Microsoft Power BI'], 'Data Visualization', 'Data & Analytics', 'Data & Analytics > Data Visualization > Power BI', ARRAY['Data Analysis'], 'An interactive data visualization software product developed by Microsoft with a primary focus on business intelligence.'),

-- Tools & Platforms
('Git', ARRAY[], 'Version Control', 'Tools & Platforms', 'Tools & Platforms > Version Control > Git', ARRAY['Software Development'], 'Software for tracking changes in any set of files, usually used for coordinating work among programmers collaboratively developing source code during software development.'),
('GitHub', ARRAY[], 'Version Control', 'Tools & Platforms', 'Tools & Platforms > Version Control > GitHub', ARRAY['Git', 'Software Development'], 'A provider of Internet hosting for software development and version control using Git.'),
('Jira', ARRAY['Atlassian Jira'], 'Project Management Tools', 'Tools & Platforms', 'Tools & Platforms > Project Management Tools > Jira', ARRAY['Agile Methodology', 'Project Management'], 'A proprietary issue tracking product developed by Atlassian that allows bug tracking and agile project management.')
ON CONFLICT (canonical_name) DO NOTHING;
