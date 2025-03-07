import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaGithub,
  FaChartLine,
  FaUniversity,
  FaIndustry,
  FaMicroscope,
  FaRobot,
} from 'react-icons/fa';

// Animation Variants
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6 },
  },
};

const fadeIn = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.6 },
  },
};

const timelineItemVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.6, delay: i * 0.2 },
  }),
};

// Key Highlights Data (for horizontal cards)
const highlightsData = [
  {
    icon: <FaChartLine className="text-4xl text-indigo-400 mb-4" />,
    title: "Huge Economic Impact",
    description:
      "AI is projected to add USD 967 billion to India's economy by 2035, reshaping industries and job markets.",
  },
  {
    icon: <FaRobot className="text-4xl text-indigo-400 mb-4" />,
    title: "Rapid Adoption",
    description:
      "From healthcare to agriculture, machine learning solutions are transforming traditional practices.",
  },
  {
    icon: <FaMicroscope className="text-4xl text-indigo-400 mb-4" />,
    title: "Cutting-Edge Research",
    description:
      "Indian institutes and companies are publishing impactful papers and patents, contributing to global AI knowledge.",
  },
  {
    icon: <FaIndustry className="text-4xl text-indigo-400 mb-4" />,
    title: "Vibrant Startup Scene",
    description:
      "India's thriving AI startup ecosystem addresses diverse challenges, from language processing to supply-chain.",
  },
];

// Expanded Timeline Data
const timelineData = [
  {
    year: "1960s–1980s",
    title: "Foundations & Early Institutions",
    description:
      "Development of TIFRAC laid groundwork in computing. IISc & early CS programs shaped AI research culture.",
  },
  {
    year: "1990s",
    title: "Growth & Acceleration",
    description:
      "Optical Character Recognition projects and Knowledge Based Systems signaled India's ML momentum.",
  },
  {
    year: "2001",
    title: "Big Data & Bioinformatics",
    description:
      "The Human Genome Project spurred breakthroughs in bioinformatics, leveraging India's IT expertise.",
  },
  {
    year: "2019",
    title: "Healthcare Innovations",
    description:
      "AI-driven screening for diabetic retinopathy at Madurai hospital showed real-world social impact.",
  },
  {
    year: "Present",
    title: "Global Leadership",
    description:
      "Indian startups, researchers, and government policies are shaping AI's future on the world stage.",
  },
];

// Sample Institutions (Cards Section)
const institutionsData = [
  {
    icon: <FaUniversity className="text-indigo-400 text-3xl mb-4" />,
    name: "Indian Institutes of Technology",
    description:
      "IITs across India house cutting-edge AI labs, training future ML experts and driving groundbreaking research.",
  },
  {
    icon: <FaUniversity className="text-indigo-400 text-3xl mb-4" />,
    name: "Indian Institute of Science (IISc)",
    description:
      "A premier research hub pushing boundaries in AI, data science, and computational biology.",
  },
  {
    icon: <FaUniversity className="text-indigo-400 text-3xl mb-4" />,
    name: "Google Research India",
    description:
      "Focusing on ML, computer vision, and NLP, with a diverse team tackling real-world problems.",
  },
  {
    icon: <FaUniversity className="text-indigo-400 text-3xl mb-4" />,
    name: "Microsoft Research India",
    description:
      "Innovations in AI for healthcare, agriculture, and accessibility, exemplifying social good.",
  },
];

const MLPresentation = () => {
  return (
    <section className="bg-gray-900 text-gray-200">
      {/* GitHub Link at Top */}
      <motion.div
        className="py-3 bg-gray-800 text-center"
        variants={fadeIn}
        initial="hidden"
        animate="visible"
      >
        <a
          href="https://github.com/lossfunk/indiaml-tracker/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 transition-colors"
        >
          <FaGithub className="mr-2" />
          View Research Data & Pipelines on GitHub
        </a>
        <p className="text-xs text-gray-400 mt-1">
          Explore data pipelines and research materials for India's ML landscape
        </p>
      </motion.div>

      {/* Hero / Intro Section */}
      <motion.div
        className="max-w-5xl mx-auto py-16 px-4 text-center"
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
      >
        <h1 className="text-4xl font-bold text-white">
          India's Rise in Machine Learning
        </h1>
        <p className="mt-4 text-lg text-gray-400 max-w-3xl mx-auto">
          Machine learning (ML) is rapidly transforming our world, with India
          emerging as a key contributor to this technological revolution. From
          pioneering research in the 1960s to cutting-edge innovations today,
          India's AI journey is poised to shape the global future.
        </p>
      </motion.div>

      {/* Horizontal Cards (previously Carousel) */}
      <motion.div
        className="max-w-6xl mx-auto px-4 py-8"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <h2 className="text-2xl font-bold text-indigo-400 mb-8 text-center">
          Key Highlights
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {highlightsData.map((item, index) => (
            <motion.div
              key={index}
              className="bg-gray-800 rounded-lg p-6 flex flex-col items-center text-center h-full"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
            >
              {item.icon}
              <h3 className="text-xl font-semibold mb-2">
                {item.title}
              </h3>
              <p className="text-gray-400">
                {item.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Timeline Section */}
      <motion.div
        className="max-w-5xl mx-auto py-16 px-4"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <h2 className="text-2xl font-bold text-indigo-400 mb-8 text-center">
          Historical Timeline
        </h2>
        <div className="relative border-l border-gray-700 ml-6">
          {timelineData.map((item, index) => (
            <motion.div
              key={index}
              className="relative pl-8 mb-10"
              variants={timelineItemVariants}
              custom={index}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              {/* Dot Indicator */}
              <span className="absolute w-3 h-3 rounded-full bg-indigo-400 top-2 left-[-5px]" />
              {/* Content */}
              <time className="block text-sm font-medium text-gray-500 mb-1">
                {item.year}
              </time>
              <h3 className="text-xl font-semibold text-gray-100">
                {item.title}
              </h3>
              <p className="text-gray-400 mt-2">
                {item.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Institutions / Cards Section */}
      <motion.div
        className="max-w-5xl mx-auto px-4 pb-16"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <h2 className="text-2xl font-bold text-indigo-400 mb-8 text-center">
          Leading Institutions & Labs
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {institutionsData.map((inst, idx) => (
            <div
              key={idx}
              className="bg-gray-800 rounded-lg p-6 shadow hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col items-center text-center">
                {inst.icon}
                <h3 className="text-xl font-bold mb-2 text-gray-100">
                  {inst.name}
                </h3>
                <p className="text-gray-400">{inst.description}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
};

export default MLPresentation;