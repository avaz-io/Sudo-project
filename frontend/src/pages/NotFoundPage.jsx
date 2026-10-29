import { Link } from 'react-router'
import Feedback from '../components/Feedback.jsx'
export default function NotFoundPage() { return <Feedback title="This path leads somewhere else."><p>The page you are looking for does not exist.</p><Link className="button" to="/">Back to campus ↗</Link></Feedback> }
