// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title DecentralizedVPN
 * @dev Smart contract for decentralized VPN management
 * @author VPN Automation Team
 */
contract DecentralizedVPN is ReentrancyGuard, Pausable, Ownable {
    using Counters for Counters.Counter;
    
    // Events
    event UserRegistered(address indexed user, uint256 userId, string username);
    event UserSubscriptionUpdated(address indexed user, uint256 planId, uint256 expiryTime);
    event PaymentProcessed(address indexed user, uint256 amount, uint256 planId);
    event NodeRegistered(address indexed node, string ipAddress, uint256 bandwidth);
    event NodeRemoved(address indexed node);
    event ConnectionEstablished(address indexed user, address indexed node, uint256 timestamp);
    event ConnectionTerminated(address indexed user, address indexed node, uint256 timestamp);
    
    // Structs
    struct User {
        uint256 userId;
        string username;
        uint256 currentPlanId;
        uint256 subscriptionExpiry;
        uint256 totalDataUsed;
        uint256 totalConnections;
        bool isActive;
        uint256 reputation;
        uint256 lastActivity;
    }
    
    struct Plan {
        uint256 planId;
        string name;
        uint256 price;
        uint256 dataLimit;
        uint256 speedLimit;
        uint256 duration;
        bool isActive;
    }
    
    struct Node {
        address nodeAddress;
        string ipAddress;
        uint256 bandwidth;
        uint256 totalConnections;
        uint256 totalDataTransferred;
        uint256 reputation;
        bool isActive;
        uint256 lastHeartbeat;
    }
    
    struct Connection {
        address user;
        address node;
        uint256 startTime;
        uint256 dataTransferred;
        bool isActive;
    }
    
    // State variables
    Counters.Counter private _userIdCounter;
    Counters.Counter private _planIdCounter;
    Counters.Counter private _connectionIdCounter;
    
    mapping(address => User) public users;
    mapping(uint256 => Plan) public plans;
    mapping(address => Node) public nodes;
    mapping(uint256 => Connection) public connections;
    mapping(address => uint256[]) public userConnections;
    mapping(address => uint256[]) public nodeConnections;
    
    // Token for payments
    IERC20 public paymentToken;
    
    // Constants
    uint256 public constant MINIMUM_STAKE = 1000 * 10**18; // 1000 tokens
    uint256 public constant REPUTATION_THRESHOLD = 50;
    uint256 public constant HEARTBEAT_INTERVAL = 300; // 5 minutes
    
    // Modifiers
    modifier onlyRegisteredUser() {
        require(users[msg.sender].isActive, "User not registered");
        _;
    }
    
    modifier onlyActiveNode() {
        require(nodes[msg.sender].isActive, "Node not active");
        _;
    }
    
    modifier onlyValidPlan(uint256 planId) {
        require(plans[planId].isActive, "Plan not active");
        _;
    }
    
    modifier onlySubscriptionActive() {
        require(users[msg.sender].subscriptionExpiry > block.timestamp, "Subscription expired");
        _;
    }
    
    constructor(address _paymentToken) {
        paymentToken = IERC20(_paymentToken);
        _initializeDefaultPlans();
    }
    
    /**
     * @dev Initialize default subscription plans
     */
    function _initializeDefaultPlans() internal {
        _createPlan("Basic", 10 * 10**18, 10 * 10**9, 1000 * 10**6, 30 days);
        _createPlan("Premium", 25 * 10**18, 50 * 10**9, 5000 * 10**6, 30 days);
        _createPlan("Enterprise", 100 * 10**18, 100 * 10**9, 10000 * 10**6, 30 days);
    }
    
    /**
     * @dev Register a new user
     * @param username User's display name
     */
    function registerUser(string memory username) external whenNotPaused {
        require(bytes(username).length > 0, "Username cannot be empty");
        require(!users[msg.sender].isActive, "User already registered");
        
        _userIdCounter.increment();
        uint256 userId = _userIdCounter.current();
        
        users[msg.sender] = User({
            userId: userId,
            username: username,
            currentPlanId: 0,
            subscriptionExpiry: 0,
            totalDataUsed: 0,
            totalConnections: 0,
            isActive: true,
            reputation: 100,
            lastActivity: block.timestamp
        });
        
        emit UserRegistered(msg.sender, userId, username);
    }
    
    /**
     * @dev Subscribe to a plan
     * @param planId ID of the plan to subscribe to
     */
    function subscribeToPlan(uint256 planId) 
        external 
        onlyRegisteredUser 
        onlyValidPlan(planId) 
        nonReentrant 
    {
        Plan memory plan = plans[planId];
        
        // Check if user has sufficient tokens
        require(paymentToken.balanceOf(msg.sender) >= plan.price, "Insufficient tokens");
        
        // Transfer tokens
        require(paymentToken.transferFrom(msg.sender, address(this), plan.price), "Payment failed");
        
        // Update user subscription
        User storage user = users[msg.sender];
        user.currentPlanId = planId;
        user.subscriptionExpiry = block.timestamp + plan.duration;
        
        emit UserSubscriptionUpdated(msg.sender, planId, user.subscriptionExpiry);
        emit PaymentProcessed(msg.sender, plan.price, planId);
    }
    
    /**
     * @dev Register a new VPN node
     * @param ipAddress Node's IP address
     * @param bandwidth Node's bandwidth capacity
     */
    function registerNode(string memory ipAddress, uint256 bandwidth) 
        external 
        whenNotPaused 
        nonReentrant 
    {
        require(bytes(ipAddress).length > 0, "IP address cannot be empty");
        require(bandwidth > 0, "Bandwidth must be greater than 0");
        require(!nodes[msg.sender].isActive, "Node already registered");
        
        // Require minimum stake
        require(paymentToken.balanceOf(msg.sender) >= MINIMUM_STAKE, "Insufficient stake");
        
        nodes[msg.sender] = Node({
            nodeAddress: msg.sender,
            ipAddress: ipAddress,
            bandwidth: bandwidth,
            totalConnections: 0,
            totalDataTransferred: 0,
            reputation: 100,
            isActive: true,
            lastHeartbeat: block.timestamp
        });
        
        emit NodeRegistered(msg.sender, ipAddress, bandwidth);
    }
    
    /**
     * @dev Remove a VPN node
     */
    function removeNode() external onlyActiveNode {
        Node storage node = nodes[msg.sender];
        node.isActive = false;
        
        emit NodeRemoved(msg.sender);
    }
    
    /**
     * @dev Establish a VPN connection
     * @param nodeAddress Address of the node to connect to
     */
    function establishConnection(address nodeAddress) 
        external 
        onlyRegisteredUser 
        onlySubscriptionActive 
    {
        require(nodes[nodeAddress].isActive, "Node not active");
        require(users[msg.sender].reputation >= REPUTATION_THRESHOLD, "Insufficient reputation");
        
        // Check data limits
        Plan memory plan = plans[users[msg.sender].currentPlanId];
        require(users[msg.sender].totalDataUsed < plan.dataLimit, "Data limit exceeded");
        
        _connectionIdCounter.increment();
        uint256 connectionId = _connectionIdCounter.current();
        
        connections[connectionId] = Connection({
            user: msg.sender,
            node: nodeAddress,
            startTime: block.timestamp,
            dataTransferred: 0,
            isActive: true
        });
        
        // Update user and node statistics
        users[msg.sender].totalConnections++;
        users[msg.sender].lastActivity = block.timestamp;
        nodes[nodeAddress].totalConnections++;
        
        userConnections[msg.sender].push(connectionId);
        nodeConnections[nodeAddress].push(connectionId);
        
        emit ConnectionEstablished(msg.sender, nodeAddress, block.timestamp);
    }
    
    /**
     * @dev Terminate a VPN connection
     * @param connectionId ID of the connection to terminate
     * @param dataTransferred Amount of data transferred during connection
     */
    function terminateConnection(uint256 connectionId, uint256 dataTransferred) 
        external 
        onlyActiveNode 
    {
        Connection storage connection = connections[connectionId];
        require(connection.isActive, "Connection not active");
        require(connection.node == msg.sender, "Not authorized");
        
        connection.isActive = false;
        connection.dataTransferred = dataTransferred;
        
        // Update user data usage
        users[connection.user].totalDataUsed += dataTransferred;
        nodes[msg.sender].totalDataTransferred += dataTransferred;
        
        emit ConnectionTerminated(connection.user, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Update node heartbeat
     */
    function updateHeartbeat() external onlyActiveNode {
        nodes[msg.sender].lastHeartbeat = block.timestamp;
    }
    
    /**
     * @dev Rate a connection (for reputation system)
     * @param connectionId ID of the connection to rate
     * @param rating Rating from 1-5
     */
    function rateConnection(uint256 connectionId, uint256 rating) 
        external 
        onlyRegisteredUser 
    {
        require(rating >= 1 && rating <= 5, "Invalid rating");
        
        Connection storage connection = connections[connectionId];
        require(connection.user == msg.sender, "Not your connection");
        require(!connection.isActive, "Connection still active");
        
        // Update reputation based on rating
        uint256 reputationChange = (rating - 3) * 10; // -20 to +20
        users[msg.sender].reputation = _clamp(users[msg.sender].reputation + reputationChange, 0, 1000);
        nodes[connection.node].reputation = _clamp(nodes[connection.node].reputation + reputationChange, 0, 1000);
    }
    
    /**
     * @dev Create a new subscription plan (owner only)
     */
    function createPlan(
        string memory name,
        uint256 price,
        uint256 speedLimit,
        uint256 dataLimit,
        uint256 duration
    ) external onlyOwner {
        _createPlan(name, price, speedLimit, dataLimit, duration);
    }
    
    function _createPlan(
        string memory name,
        uint256 price,
        uint256 speedLimit,
        uint256 dataLimit,
        uint256 duration
    ) internal {
        _planIdCounter.increment();
        uint256 planId = _planIdCounter.current();
        
        plans[planId] = Plan({
            planId: planId,
            name: name,
            price: price,
            dataLimit: dataLimit,
            speedLimit: speedLimit,
            duration: duration,
            isActive: true
        });
    }
    
    /**
     * @dev Get user information
     */
    function getUserInfo(address userAddress) external view returns (User memory) {
        return users[userAddress];
    }
    
    /**
     * @dev Get node information
     */
    function getNodeInfo(address nodeAddress) external view returns (Node memory) {
        return nodes[nodeAddress];
    }
    
    /**
     * @dev Get connection information
     */
    function getConnectionInfo(uint256 connectionId) external view returns (Connection memory) {
        return connections[connectionId];
    }
    
    /**
     * @dev Get user's active connections
     */
    function getUserConnections(address userAddress) external view returns (uint256[] memory) {
        return userConnections[userAddress];
    }
    
    /**
     * @dev Get node's active connections
     */
    function getNodeConnections(address nodeAddress) external view returns (uint256[] memory) {
        return nodeConnections[nodeAddress];
    }
    
    /**
     * @dev Check if node is healthy (heartbeat within interval)
     */
    function isNodeHealthy(address nodeAddress) external view returns (bool) {
        Node memory node = nodes[nodeAddress];
        return node.isActive && (block.timestamp - node.lastHeartbeat) <= HEARTBEAT_INTERVAL;
    }
    
    /**
     * @dev Pause the contract (emergency)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Withdraw accumulated fees (owner only)
     */
    function withdrawFees() external onlyOwner {
        uint256 balance = paymentToken.balanceOf(address(this));
        require(balance > 0, "No fees to withdraw");
        require(paymentToken.transfer(owner(), balance), "Withdrawal failed");
    }
    
    /**
     * @dev Utility function to clamp values
     */
    function _clamp(uint256 value, uint256 min, uint256 max) internal pure returns (uint256) {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    }
}
