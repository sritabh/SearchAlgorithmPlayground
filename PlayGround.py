import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame 
import json
from World import World
from Blocks import *
from config import *

class Button:
    def __init__(self,world,pos,size,bgColor,color,label="Button",labelSize:float=0.5):
        self._world = world
        self._pos = pos
        self.size = size
        self._color = color
        self._fontSize = int(size[1]*labelSize)
        self._label = label
        self._font = pygame.font.SysFont('Arial', self._fontSize)
        self._bgColor = bgColor
        

    def draw_node(self):
        pos = self._pos+self.size
        self.pgObj = pygame.draw.rect(self._world.win, self._bgColor, pygame.Rect(pos),  100, 3)
        labelLength = self._fontSize*len(self._label)
        text = self._font.render(self._label, True, self._color)
        text_rect = text.get_rect(center = self.pgObj.center)
        self._world.win.blit(text, text_rect)
    def isClicked(self,collidePos):
        if self.pgObj.collidepoint(collidePos):
            return True
        else:
            return False


class PlayGround:
    def __init__(self,world:World=None,startNodeID:tuple=None,goalNodeIDs=None,blocks_dimension = BLOCKS_DIMENSION,block_size = BLOCK_SIZE):
        """
        Creates a playground with the given world if no parameter given creates a default world
        blocks_dimension: Total blocks that will be shown on the screen as (rows,cols)
        block_size: size of each block
        NOTE: Parameters can be modified in config file as well
        """
        pygame.init() #Initialise the pygame
        pygame.display.set_caption(TITLE) #set the title
        self.world = World(blocks_dimension,block_size,BOTTOM_PANEL_HEIGHT,GRID_WIDTH,BACKGROUND_COLOR,GRID_COLOR,MARGIN) if world is None else world
        self._isClicked = False
        self._running = False
        self._selectedNode = None #This is the node which is selected, will help in moving the nodes around
        #A Playground consist of a start node and a goal node always
        self._startNode = Node(self.world.getBlock((0,0)),'S',SPECIAL_NODE_BORDER_COLOR,SPECIAL_NODE_COLOR,3,True) if startNodeID is None else world.getNode(startNodeID)
        self._goalNode = Node(self.world.getBlock((len(self.world.available_blocks)-1,len(self.world.available_blocks[0])-1)),'G',SPECIAL_NODE_BORDER_COLOR,SPECIAL_NODE_COLOR,3,True) if goalNodeIDs is None else world.getNode(goalNodeIDs) 
        #Add the nodes in the world
        self.world.add_node(self._startNode)
        self.world.add_node(self._goalNode)
        self._isDragging = False #True when clicked and mouse is dragging
        self._selectedEdge = None
        self._selectedBlock = None
        self.startButton = None
        self._createControls()
    
    @classmethod
    def fromfilename(cls,filename:str):
        """
        Returns a playground object initialised from the values given in filename
        """
        file = MY_WORK_DIR+filename
        pygame.init()
        try:
            with open(file,'r') as f:
                playGroundData = json.load(f)
                #Create world
                world = World.fromdict(dict(playGroundData['world']))
                startNodeID = tuple(eval(playGroundData['startNode']))
                goalNodeID = tuple(eval(playGroundData['goalNode']))
                #Create special nodes
        except FileNotFoundError:
            msg = "Unable to locate the file '{}' at '{}'\nMake sure the given filename is present at the given location".format(filename,file)
            raise FileNotFoundError(msg)
        return cls(world,startNodeID,goalNodeID)
    def _createControls(self):
        """
        Generates button to control the playground
        """
        print("Button created")
        height = int(BOTTOM_PANEL_HEIGHT/3)
        width = int(height*2)
        pos_x = int((self.world.win.get_size()[0]-width)/2)
        pos_y = (self.world.win.get_size()[1]-int((BOTTOM_PANEL_HEIGHT)/2))
        print(pos_x,pos_y)
        self.startButton = Button(self.world,(pos_x,pos_y),(width,height),BUTTON_COLOR_PRIMARY,GRAY,"Run")
        ##Secondary buttons
        """height = int(BOTTOM_PANEL_HEIGHT/3.5)
        width = int(height*1.8)
        pos_x = int((width)/2)
        self.selectStartButton = Button(self.world,(pos_x,pos_y),(width,height),BUTTON_COLOR_SECONDARY,GRAY,"Select Start",0.3)
        pos_x = int(self.world.win.get_size()[0] - (width)/2) - width
        self.selectGoalButton = Button(self.world,(pos_x,pos_y),(width,height),BUTTON_COLOR_SECONDARY,GRAY,"Select Goal",0.3)"""



    def _drawButtons(self):
        self.startButton.draw_node()
        """self.selectGoalButton.draw_node()
        self.selectStartButton.draw_node()"""

    def _genLabel(self):
        def _nextLabel(label = ""):
            """
            A utility function to genLabel
            Counting with alphabet system
            Generates next label 
            """
            revL = [char for char in label[::-1]]
            n = len(revL)
            if n==0:
                return 'A'
            found = False
            for i in range(0,n):
                nextChar = chr(ord(revL[i])+1)
                if(nextChar <= 'Z'):
                    found = True
                    revL[i] = nextChar
                    break
                else:
                    revL[i] = 'A'
            if not found:
                revL.append('A')
            return ''.join(revL[::-1])
        """
        Function generates a label for a node which is not already there in the grid
        """
        label = "A"
        while label in self.world.getNodes().values():
            label = _nextLabel(label)
        return label

    def _getClickedEdge(self,pos)->Edge:
        edges = self.world.getEdges()
        if edges:
            for edge in edges.values():
                if edge.collidePoint(pos):
                    return edge
        
        return None
    def _getClickedBlock(self,pos)->Block:
        """
        Click Handler, checks if the click is button node or simple node and manages accordingly
        """

        blocks = self.world.available_blocks
        if not blocks:
            raise ValueError("Blocks are not initialised")
        else:
            for row in blocks:
                for block in row:
                    if block.pgObj.collidepoint(pos):
                        return block
    def _dragNode(self,newBlock):
        """
        Drags node to newBlock location
        """
        if self._isClicked and self._selectedNode is not None and not newBlock.hasNode():
            #Update node location
            self.world.update_node_loc(self._selectedNode,newBlock)
            #print("Dragging to {}".format(newBlock))
    def _handleClicks(self,event):
        """
        Handles any click made on the screen
        """
        if self.startButton.isClicked(event.pos):
            self.saveWork("TestGraph.json")
            return
        block = self._getClickedBlock(event.pos)
        if block is not None and not block.hasNode() and not self._isDragging:
            print(block.hasNode())
            #No selected node
            if self._selectedNode is not None:
                self._selectedNode.selected(False)
                self._selectedNode = None

            edge = self._getClickedEdge(event.pos)
            if edge is not None:
                self._selectedEdge = edge
                #print(self.world.getEdges())
                return
        if block is not None:
            self._dragNode(block)
            if not self._isDragging:
                if block.hasNode():
                    if self._selectedBlock is not None:
                        self._selectedBlock.highlight(False)
                        self._selectedBlock = None

                    if self._selectedNode is not None and self._selectedNode != self.world.getNode(block.id):
                        self._selectedNode.selected(False) #Remove any selected node, probably help in creating no further edges without knowing
                        #If the nodes are not same then create an edge
                        if self.world.getNode(block.id) not in self._selectedNode.get_neighbours():
                            edge = Edge(self._selectedNode,self.world.getNode(block.id))
                            ##Add new edge to the world
                            self.world.add_edge(edge)
                        self._selectedNode = None

                    elif self._selectedNode is not None:
                        self._selectedNode.selected(False)
                    else:
                        self._selectedNode = self.world.getNode(block.id)
                        self._selectedNode.selected(True)

                else:
                    if self._selectedBlock is not None:
                        self._selectedBlock.highlight(False) #Remove previous highlighted block
                        if block == self._selectedBlock:
                            self._selectedNode = Node(block,self._genLabel(),NODE_BORDER_COLOR,NODE_COLOR)
                            self.world.add_node(self._selectedNode) #Add the new node to world
                            self._selectedNode.selected(False)
                            self._selectedBlock = None
                        else:
                            self._selectedBlock = block
                            self._selectedBlock.highlight(True)
                    else:
                        self._selectedBlock = block
                        self._selectedBlock.highlight(True)
                    self._selectedNode = None
            if not self._isDragging:
                print(block)
        else:
            #If the click is made somewhere outside a grid
            if self._selectedBlock is not None:
                self._selectedBlock.highlight(False)
                self._selectedBlock = None
            if self._selectedNode is not None:
                self._selectedNode.selected(False)
                self._selectedNode = None


    def eventHandler(self,event):
        """
        Handles all the events
        """
        if self._selectedNode is not None:
            if not self._selectedNode.handle_event(self.world,event):
                self._selectedNode.selected(False)
                self._selectedNode = None
        elif self._selectedEdge is not None:
            if not self._selectedEdge.handle_event(self.world,event):
                self._selectedEdge = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handleClicks(event)
            self._isClicked = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self._isClicked = False
        elif event.type == pygame.MOUSEMOTION:
            if self._isClicked:
                self._isDragging = True
                self._handleClicks(event)
            else:
                self._isDragging = False
    def delay(self,millisecond:int):
        """
        Delays the playground and the program
        """
        pygame.time.delay(millisecond)
        self.drawScenary() #Draw scenary even if the program is being paused
    def drawScenary(self):
        """
        Draw the elements of the world and world along with it
        NOTE: If the control is taken away for a while, make sure to drawScenary to reflect the changes in the world
        """
        self.world.create_grids()
        if self.startButton is not None:
            self._drawButtons()
        pygame.display.update()

    def MoveGen(self,node:Node)->list:
        """
        Returns a list of neighbouring nodes in sorted order of their label
        """
        return node.get_neighbours()
    def get_edge(self,nodeStart:Node,nodeEnd:Node)->Edge:
        """
        Returns an edge between the two nodes if it exists
        """
        return self.world.getEdge(nodeStart.id,nodeEnd.id)
    def getGoalNode(self)->Node:
        """
        Returns goal node in the world
        """
        return self._goalNode
    
    def getStartNode(self)->Node:
        """
        Returns start node in the world
        """
        return self._startNode
    
    def saveWork(self,filename:str=None):
        """
        Saves the current graph to a file with given filename
        If no filename is provided files are saved with some meaningful name
        """
        from datetime import datetime as dt
        # Getting current date and time
        now = dt.now()
        if filename is None:
            filename = "Graph "+now.strftime("%d-%m-%Y %H:%M:%S")+".json" #Save data with current date and time
        location = os.path.join(os.getcwd(),MY_WORK_DIR)
        file = os.path.join(location, filename)
        try:
            with open(file,'w') as f:
                val = str(self.to_dict())
                f.write(json.dumps(self.to_dict(), indent=4))
                print("Work saved at: {}".format(file))
        except FileNotFoundError:
            #Directory not found
            os.mkdir(location) #Create the directory
            self.saveWork(filename)


    def to_dict(self)->dict:
        """
        Returns parameters and value as dictionary
        """
        playground = {
            'world':self.world.to_dict(),
            'startNode':str(self._startNode.id),
            'goalNode':str(self._goalNode.id)
        }
        return playground
    
    def run(self):
        """
        Start the playground to play with
        """
        clock = pygame.time.Clock()
        icon = pygame.image.load('img/icon.png')
        pygame.display.set_icon(icon)
        running = True
        print("Search Algorithm PlayGround Tool created by Sritabh Priyadarshi using pygame.\nVisit https://github.com/SobyDamn/SearchAlgorithmVisualisation for more info.")
        while running:
            self.drawScenary()
            for event in pygame.event.get():  
                if event.type == pygame.QUIT:  
                    running = False
                else:
                    self.eventHandler(event)
            clock.tick(60)
        pygame.quit()


PG = PlayGround.fromfilename("TestGraph.json")
PG.run()